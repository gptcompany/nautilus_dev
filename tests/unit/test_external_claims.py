"""
Unit tests for ExternalOrderClaimConfig.

Tests cover:
- T027: Basic configuration
- T028: claim_all/instrument_ids mutual exclusion
"""


import pytest

from config.reconciliation.external_claims import ExternalOrderClaimConfig


class TestExternalOrderClaimConfig:
    """T027: Test ExternalOrderClaimConfig basic functionality."""

    def test_default_values(self):
        """Verify default values."""
        config = ExternalOrderClaimConfig()

        assert config.instrument_ids == []
        assert config.claim_all is False

    def test_with_instrument_ids(self):
        """Config accepts valid instrument IDs."""
        config = ExternalOrderClaimConfig(
            instrument_ids=[
                "BTCUSDT-PERP.BINANCE",
                "ETHUSDT-PERP.BINANCE",
            ],
        )

        assert len(config.instrument_ids) == 2
        assert "BTCUSDT-PERP.BINANCE" in config.instrument_ids

    def test_with_claim_all(self):
        """Config accepts claim_all=True."""
        config = ExternalOrderClaimConfig(claim_all=True)

        assert config.claim_all is True
        assert config.instrument_ids == []

    def test_config_is_immutable(self):
        """Config should be frozen (immutable)."""
        config = ExternalOrderClaimConfig()
        with pytest.raises(Exception):
            config.claim_all = True


class TestExternalOrderClaimConfigValidation:
    """T028: Test claim_all/instrument_ids mutual exclusion."""

    def test_cannot_set_both_claim_all_and_instrument_ids(self):
        """Cannot set both claim_all=True and specific instrument_ids."""
        with pytest.raises(ValueError, match="Cannot specify"):
            ExternalOrderClaimConfig(
                claim_all=True,
                instrument_ids=["BTCUSDT-PERP.BINANCE"],
            )

    def test_instrument_id_format_validation(self):
        """Instrument IDs must match expected format."""
        # Valid formats
        valid_ids = [
            "BTCUSDT-PERP.BINANCE",
            "ETHUSDT.BINANCE",
            "BTC_USDT.BYBIT",
            "ES-Z24.CME",
        ]
        for id_ in valid_ids:
            config = ExternalOrderClaimConfig(instrument_ids=[id_])
            assert id_ in config.instrument_ids

        # Invalid formats
        invalid_ids = [
            "btcusdt-perp.binance",  # lowercase
            "BTCUSDT-PERP",  # missing venue
            ".BINANCE",  # missing instrument
            "BTCUSDT-PERP.",  # missing venue after dot
        ]
        for id_ in invalid_ids:
            with pytest.raises(ValueError, match="Invalid instrument ID format"):
                ExternalOrderClaimConfig(instrument_ids=[id_])

    def test_empty_instrument_ids_allowed(self):
        """Empty instrument_ids list is valid."""
        config = ExternalOrderClaimConfig(instrument_ids=[])
        assert config.instrument_ids == []

    def test_get_external_order_claims_with_instrument_ids(self):
        """get_external_order_claims returns instrument_ids."""
        config = ExternalOrderClaimConfig(
            instrument_ids=[
                "BTCUSDT-PERP.BINANCE",
                "ETHUSDT-PERP.BINANCE",
            ],
        )
        claims = config.get_external_order_claims()
        assert claims == ["BTCUSDT-PERP.BINANCE", "ETHUSDT-PERP.BINANCE"]

    def test_get_external_order_claims_with_claim_all(self):
        """get_external_order_claims returns None for claim_all."""
        config = ExternalOrderClaimConfig(claim_all=True)
        claims = config.get_external_order_claims()
        assert claims is None  # Indicates "claim all"
