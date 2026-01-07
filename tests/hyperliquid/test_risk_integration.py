"""Tests for Hyperliquid RiskManager integration (Spec 021 - US4).

Tests the strategy configuration and RiskManager integration.
"""

from decimal import Decimal

import pytest
from nautilus_trader.model.identifiers import InstrumentId

from risk import RiskConfig, StopLossType
from strategies.hyperliquid.base_strategy import HyperliquidBaseStrategy
from strategies.hyperliquid.config import HyperliquidStrategyConfig


class TestHyperliquidStrategyConfig:
    """Tests for HyperliquidStrategyConfig."""

    def test_default_values(self):
        """Default configuration is valid."""
        config = HyperliquidStrategyConfig()

        assert config.instrument_id == "BTC-USD-PERP.HYPERLIQUID"
        assert config.order_size == Decimal("0.001")
        assert config.max_position_size == Decimal("0.1")
        assert isinstance(config.risk, RiskConfig)

    def test_custom_instrument(self):
        """Custom instrument ID is used."""
        config = HyperliquidStrategyConfig(
            instrument_id="ETH-USD-PERP.HYPERLIQUID",
        )

        assert config.instrument_id == "ETH-USD-PERP.HYPERLIQUID"

    def test_custom_order_size(self):
        """Custom order size is used."""
        config = HyperliquidStrategyConfig(
            order_size=Decimal("0.01"),
        )

        assert config.order_size == Decimal("0.01")

    def test_custom_max_position_size(self):
        """Custom max position size is used."""
        config = HyperliquidStrategyConfig(
            max_position_size=Decimal("1.0"),
        )

        assert config.max_position_size == Decimal("1.0")

    def test_custom_risk_config(self):
        """Custom risk config is used."""
        risk = RiskConfig(
            stop_loss_pct=Decimal("0.03"),
            stop_loss_type=StopLossType.LIMIT,
        )
        config = HyperliquidStrategyConfig(risk=risk)

        assert config.risk.stop_loss_pct == Decimal("0.03")
        assert config.risk.stop_loss_type == StopLossType.LIMIT

    def test_order_size_must_be_positive(self):
        """Order size must be positive."""
        with pytest.raises(ValueError):
            HyperliquidStrategyConfig(order_size=Decimal("0"))

    def test_max_position_size_must_be_positive(self):
        """Max position size must be positive."""
        with pytest.raises(ValueError):
            HyperliquidStrategyConfig(max_position_size=Decimal("-1"))

    def test_get_risk_config_with_limits(self):
        """get_risk_config_with_limits applies position limits."""
        config = HyperliquidStrategyConfig(
            instrument_id="BTC-USD-PERP.HYPERLIQUID",
            max_position_size=Decimal("0.5"),
        )

        risk_with_limits = config.get_risk_config_with_limits()

        assert risk_with_limits.max_position_size is not None
        assert "BTC-USD-PERP.HYPERLIQUID" in risk_with_limits.max_position_size
        assert risk_with_limits.max_position_size["BTC-USD-PERP.HYPERLIQUID"] == Decimal("0.5")


class TestHyperliquidBaseStrategy:
    """Tests for HyperliquidBaseStrategy."""

    def test_initialization(self):
        """Strategy initializes correctly."""
        config = HyperliquidStrategyConfig()
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.strategy_config == config
        assert strategy.instrument_id == InstrumentId.from_str("BTC-USD-PERP.HYPERLIQUID")
        assert strategy.risk_manager is not None

    def test_risk_manager_has_config(self):
        """RiskManager receives config with position limits."""
        config = HyperliquidStrategyConfig(
            instrument_id="ETH-USD-PERP.HYPERLIQUID",
            max_position_size=Decimal("2.0"),
            risk=RiskConfig(stop_loss_pct=Decimal("0.05")),
        )
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.risk_manager.config.stop_loss_pct == Decimal("0.05")
        assert strategy.risk_manager.config.max_position_size is not None
        assert "ETH-USD-PERP.HYPERLIQUID" in strategy.risk_manager.config.max_position_size

    def test_validate_order_size_within_limits(self):
        """Order size within limits returns True."""
        config = HyperliquidStrategyConfig(max_position_size=Decimal("1.0"))
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.validate_order_size(Decimal("0.5")) is True

    def test_validate_order_size_exceeds_limits(self):
        """Order size exceeding limits returns False."""
        config = HyperliquidStrategyConfig(max_position_size=Decimal("1.0"))
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.validate_order_size(Decimal("2.0")) is False

    def test_validate_order_size_at_limit(self):
        """Order size at limit returns True."""
        config = HyperliquidStrategyConfig(max_position_size=Decimal("1.0"))
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.validate_order_size(Decimal("1.0")) is True


class TestRiskManagerIntegration:
    """Tests for RiskManager integration with strategy."""

    def test_stop_loss_enabled_by_default(self):
        """Stop-loss is enabled by default."""
        config = HyperliquidStrategyConfig()
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.risk_manager.config.stop_loss_enabled is True

    def test_custom_stop_loss_percentage(self):
        """Custom stop-loss percentage is applied."""
        config = HyperliquidStrategyConfig(
            risk=RiskConfig(stop_loss_pct=Decimal("0.03")),
        )
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.risk_manager.config.stop_loss_pct == Decimal("0.03")

    def test_trailing_stop_disabled_by_default(self):
        """Trailing stop is disabled by default."""
        config = HyperliquidStrategyConfig()
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.risk_manager.config.trailing_stop is False

    def test_trailing_stop_can_be_enabled(self):
        """Trailing stop can be enabled."""
        config = HyperliquidStrategyConfig(
            risk=RiskConfig(
                trailing_stop=True,
                trailing_distance_pct=Decimal("0.01"),
            ),
        )
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.risk_manager.config.trailing_stop is True
        assert strategy.risk_manager.config.trailing_distance_pct == Decimal("0.01")
