"""
Unit tests for RiskConfig validation.

Tests cover:
- Default values
- Valid configurations
- Invalid percentages
- Negative values
- Edge cases
"""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from risk.config import RiskConfig, StopLossType, TrailingOffsetType


class TestRiskConfigDefaults:
    """Test default configuration values."""

    def test_default_stop_loss_enabled(self) -> None:
        """Default should enable stop-loss."""
        config = RiskConfig()
        assert config.stop_loss_enabled is True

    def test_default_stop_loss_pct(self) -> None:
        """Default stop-loss percentage should be 2%."""
        config = RiskConfig()
        assert config.stop_loss_pct == Decimal("0.02")

    def test_default_stop_loss_type(self) -> None:
        """Default should use market stop orders."""
        config = RiskConfig()
        assert config.stop_loss_type == StopLossType.MARKET

    def test_default_trailing_stop_disabled(self) -> None:
        """Default should disable trailing stops."""
        config = RiskConfig()
        assert config.trailing_stop is False

    def test_default_position_limits_none(self) -> None:
        """Default should have no position limits."""
        config = RiskConfig()
        assert config.max_position_size is None
        assert config.max_total_exposure is None


class TestRiskConfigValidation:
    """Test configuration validation rules."""

    def test_stop_loss_pct_must_be_positive(self) -> None:
        """Stop-loss percentage must be > 0."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(stop_loss_pct=Decimal("0"))
        assert "greater than 0" in str(exc_info.value)

    def test_stop_loss_pct_must_be_less_than_one(self) -> None:
        """Stop-loss percentage must be < 1 (100%)."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(stop_loss_pct=Decimal("1.0"))
        assert "less than 1" in str(exc_info.value)

    def test_stop_loss_pct_negative_rejected(self) -> None:
        """Negative stop-loss percentage should be rejected."""
        with pytest.raises(ValidationError):
            RiskConfig(stop_loss_pct=Decimal("-0.02"))

    def test_trailing_distance_must_be_positive(self) -> None:
        """Trailing distance must be > 0."""
        with pytest.raises(ValidationError):
            RiskConfig(trailing_distance_pct=Decimal("0"))

    def test_trailing_distance_cannot_exceed_stop_loss(self) -> None:
        """Trailing distance must be <= stop-loss distance."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(
                trailing_stop=True,
                stop_loss_pct=Decimal("0.02"),
                trailing_distance_pct=Decimal("0.05"),  # 5% > 2%
            )
        assert "trailing_distance_pct" in str(exc_info.value)
        assert "must be <=" in str(exc_info.value)

    def test_trailing_distance_equal_to_stop_loss_valid(self) -> None:
        """Trailing distance equal to stop-loss is valid."""
        config = RiskConfig(
            trailing_stop=True,
            stop_loss_pct=Decimal("0.02"),
            trailing_distance_pct=Decimal("0.02"),
        )
        assert config.trailing_distance_pct == Decimal("0.02")

    def test_max_position_size_must_be_positive(self) -> None:
        """All position size values must be positive."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("0")})
        assert "must be positive" in str(exc_info.value)

    def test_max_position_size_negative_rejected(self) -> None:
        """Negative position sizes should be rejected."""
        with pytest.raises(ValidationError) as exc_info:
            RiskConfig(max_position_size={"BTC/USDT.BINANCE": Decimal("-1.0")})
        assert "must be positive" in str(exc_info.value)

    def test_max_total_exposure_must_be_positive(self) -> None:
        """Total exposure limit must be positive."""
        with pytest.raises(ValidationError):
            RiskConfig(max_total_exposure=Decimal("0"))

    def test_max_total_exposure_negative_rejected(self) -> None:
        """Negative total exposure should be rejected."""
        with pytest.raises(ValidationError):
            RiskConfig(max_total_exposure=Decimal("-10000"))

    def test_ou_lookback_days_minimum(self) -> None:
        """OU lookback days must be >= 7."""
        with pytest.raises(ValidationError):
            RiskConfig(ou_lookback_days=6)

    def test_ou_lookback_days_maximum(self) -> None:
        """OU lookback days must be <= 365."""
        with pytest.raises(ValidationError):
            RiskConfig(ou_lookback_days=366)


class TestRiskConfigValidCases:
    """Test valid configuration cases."""

    def test_minimal_config(self) -> None:
        """Minimal config with just stop-loss percentage."""
        config = RiskConfig(stop_loss_pct=Decimal("0.05"))
        assert config.stop_loss_pct == Decimal("0.05")

    def test_full_config(self) -> None:
        """Full configuration with all options set."""
        config = RiskConfig(
            stop_loss_enabled=True,
            stop_loss_pct=Decimal("0.03"),
            stop_loss_type=StopLossType.LIMIT,
            trailing_stop=True,
            trailing_distance_pct=Decimal("0.015"),
            trailing_offset_type=TrailingOffsetType.BASIS_POINTS,
            max_position_size={
                "BTC/USDT.BINANCE": Decimal("0.5"),
                "ETH/USDT.BINANCE": Decimal("5.0"),
            },
            max_total_exposure=Decimal("10000"),
            dynamic_boundaries=False,
            ou_lookback_days=30,
        )
        assert config.stop_loss_type == StopLossType.LIMIT
        assert config.trailing_stop is True
        assert len(config.max_position_size) == 2

    def test_position_limits_only_no_stop_loss(self) -> None:
        """Config with position limits but no stop-loss."""
        config = RiskConfig(
            stop_loss_enabled=False,
            max_position_size={"BTC/USDT.BINANCE": Decimal("1.0")},
            max_total_exposure=Decimal("50000"),
        )
        assert config.stop_loss_enabled is False
        assert config.max_position_size is not None

    def test_emulated_stop_type(self) -> None:
        """Config with emulated stop-loss type."""
        config = RiskConfig(stop_loss_type=StopLossType.EMULATED)
        assert config.stop_loss_type == StopLossType.EMULATED


class TestRiskConfigSerialization:
    """Test JSON serialization support."""

    def test_model_dump_json(self) -> None:
        """Config should serialize to JSON."""
        config = RiskConfig(
            stop_loss_pct=Decimal("0.02"),
            max_position_size={"BTC/USDT.BINANCE": Decimal("0.5")},
        )
        json_str = config.model_dump_json()
        assert '"stop_loss_pct":"0.02"' in json_str or '"stop_loss_pct": "0.02"' in json_str

    def test_model_dump_dict(self) -> None:
        """Config should dump to dict."""
        config = RiskConfig(stop_loss_pct=Decimal("0.02"))
        data = config.model_dump()
        assert data["stop_loss_pct"] == Decimal("0.02")
        assert data["stop_loss_enabled"] is True


class TestStopLossTypeEnum:
    """Test StopLossType enum."""

    def test_market_value(self) -> None:
        """MARKET enum value should be 'market'."""
        assert StopLossType.MARKET.value == "market"

    def test_limit_value(self) -> None:
        """LIMIT enum value should be 'limit'."""
        assert StopLossType.LIMIT.value == "limit"

    def test_emulated_value(self) -> None:
        """EMULATED enum value should be 'emulated'."""
        assert StopLossType.EMULATED.value == "emulated"

    def test_from_string(self) -> None:
        """Should create enum from string value."""
        assert StopLossType("market") == StopLossType.MARKET


class TestTrailingOffsetTypeEnum:
    """Test TrailingOffsetType enum."""

    def test_price_value(self) -> None:
        """PRICE enum value should be 'price'."""
        assert TrailingOffsetType.PRICE.value == "price"

    def test_basis_points_value(self) -> None:
        """BASIS_POINTS enum value should be 'basis_points'."""
        assert TrailingOffsetType.BASIS_POINTS.value == "basis_points"
