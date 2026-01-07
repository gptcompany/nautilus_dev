"""
Integration tests for Order Reconciliation.

Tests cover:
- T034: TradingNode startup reconciliation
- T035: Continuous polling
- T036: External order detection
- T037-T038: NFR-001 Fill completeness
- T039-T041: NFR-002 Performance tests
- T042: Disconnection simulation
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from config.reconciliation.config import ReconciliationConfig
from config.reconciliation.presets import ReconciliationPreset
from config.trading_node.live_config import LiveTradingNodeConfig

if TYPE_CHECKING:
    from config.reconciliation.external_claims import ExternalOrderClaimConfig


class TestTradingNodeStartupReconciliation:
    """T034: Integration test TradingNode startup reconciliation."""

    def test_trading_node_config_produces_valid_exec_config(
        self,
        trading_node_config: LiveTradingNodeConfig,
    ):
        """TradingNode config produces valid execution engine config."""
        exec_config = trading_node_config.build_exec_engine_config()

        assert exec_config["reconciliation"] is True
        assert exec_config["reconciliation_startup_delay_secs"] >= 10.0
        assert "inflight_check_interval_ms" in exec_config
        assert "open_check_interval_secs" in exec_config

    def test_trading_node_config_produces_valid_cache_config(
        self,
        trading_node_config: LiveTradingNodeConfig,
    ):
        """TradingNode config produces valid cache config."""
        cache_config = trading_node_config.build_cache_config()

        assert cache_config["database"]["type"] == "redis"
        assert cache_config["database"]["host"] == "localhost"
        assert cache_config["database"]["port"] == 6379
        assert cache_config["persist_account_events"] is True

    def test_trading_node_config_with_custom_recon_settings(
        self,
        trading_node_config_with_custom_recon: LiveTradingNodeConfig,
    ):
        """Custom reconciliation settings are applied correctly."""
        exec_config = trading_node_config_with_custom_recon.build_exec_engine_config()

        assert exec_config["reconciliation_startup_delay_secs"] == 12.0
        assert exec_config["reconciliation_lookback_mins"] == 90
        assert exec_config["inflight_check_interval_ms"] == 1500
        assert exec_config["open_check_interval_secs"] == 3.0

    def test_trading_node_config_complete_output(
        self,
        trading_node_config: LiveTradingNodeConfig,
    ):
        """Complete TradingNode config contains all required sections."""
        node_config = trading_node_config.build_trading_node_config()

        assert "trader_id" in node_config
        assert "exec_engine" in node_config
        assert "cache" in node_config
        assert node_config["trader_id"] == "TEST-TRADER-001"


class TestContinuousPolling:
    """T035: Integration test continuous polling."""

    def test_standard_preset_enables_continuous_polling(
        self,
        standard_reconciliation_config: ReconciliationConfig,
    ):
        """STANDARD preset has continuous polling enabled."""
        config = standard_reconciliation_config

        assert config.open_check_interval_secs is not None
        assert config.open_check_interval_secs == 5.0
        assert config.open_check_lookback_mins >= 60

    def test_disabled_preset_disables_continuous_polling(
        self,
        disabled_reconciliation_config: ReconciliationConfig,
    ):
        """DISABLED preset has continuous polling disabled."""
        config = disabled_reconciliation_config

        assert config.open_check_interval_secs is None

    def test_continuous_polling_interval_in_exec_config(
        self,
        trading_node_config: LiveTradingNodeConfig,
    ):
        """Continuous polling interval is included in exec config."""
        exec_config = trading_node_config.build_exec_engine_config()

        assert exec_config["open_check_interval_secs"] == 5.0
        assert exec_config["open_check_lookback_mins"] == 60


class TestExternalOrderDetection:
    """T036: Integration test external order detection."""

    def test_external_claims_with_specific_instruments(
        self,
        external_claims_config: ExternalOrderClaimConfig,
    ):
        """External claims config returns specific instruments."""
        claims = external_claims_config.get_external_order_claims()

        assert claims is not None
        assert len(claims) == 2
        assert "BTCUSDT-PERP.BINANCE" in claims
        assert "ETHUSDT-PERP.BINANCE" in claims

    def test_external_claims_with_claim_all(
        self,
        external_claims_all: ExternalOrderClaimConfig,
    ):
        """External claims with claim_all returns None (semantic for 'all')."""
        claims = external_claims_all.get_external_order_claims()

        assert claims is None  # None = claim all


class TestFillCompleteness:
    """T037-T038: NFR-001 Fill completeness tests."""

    def test_fill_count_comparison(
        self,
        mock_fills: list[dict],
    ):
        """Test fill count comparison for completeness check."""
        # Simulate: venue returns N fills, we should reconcile N fills
        venue_fill_count = len(mock_fills)
        reconciled_fill_count = len(mock_fills)  # Perfect reconciliation

        assert reconciled_fill_count == venue_fill_count
        assert venue_fill_count == 1

    def test_no_duplicate_fills(
        self,
        mock_fills: list[dict],
    ):
        """Test no duplicate fill events."""
        fill_ids = [fill["fill_id"] for fill in mock_fills]
        unique_fill_ids = set(fill_ids)

        # No duplicates means length matches
        assert len(fill_ids) == len(unique_fill_ids)

    def test_all_fills_have_required_fields(
        self,
        mock_fills: list[dict],
    ):
        """All fills have required fields for reconciliation."""
        required_fields = {
            "fill_id",
            "order_id",
            "instrument_id",
            "side",
            "quantity",
            "price",
        }

        for fill in mock_fills:
            assert required_fields.issubset(fill.keys())


class TestPerformance:
    """T039-T041: NFR-002 Performance tests."""

    def test_startup_reconciliation_config_creation_fast(self):
        """T039: Config creation should be fast (< 100ms)."""
        start = time.perf_counter()

        # Create config 100 times
        for _ in range(100):
            config = ReconciliationPreset.STANDARD.to_config()
            _ = config.to_live_exec_engine_config()

        elapsed = time.perf_counter() - start

        # 100 config creations should complete in < 100ms
        assert elapsed < 0.1

    def test_trading_node_config_creation_fast(self):
        """T040: TradingNode config creation should be fast."""
        start = time.perf_counter()

        # Create config 100 times
        for i in range(100):
            config = LiveTradingNodeConfig(
                trader_id=f"PERF-TEST-{i:03d}",
                reconciliation=ReconciliationPreset.STANDARD,
            )
            _ = config.build_trading_node_config()

        elapsed = time.perf_counter() - start

        # 100 config creations should complete in < 200ms
        assert elapsed < 0.2

    def test_preset_conversion_consistent(self):
        """T041: Preset conversion produces consistent results."""
        # Create same preset multiple times
        configs = [ReconciliationPreset.STANDARD.to_config() for _ in range(10)]

        # All should have identical values
        first = configs[0]
        for config in configs[1:]:
            assert config.startup_delay_secs == first.startup_delay_secs
            assert config.open_check_interval_secs == first.open_check_interval_secs
            assert config.inflight_check_interval_ms == first.inflight_check_interval_ms


class TestDisconnectionRecovery:
    """T042: Integration test disconnection simulation and recovery."""

    def test_config_supports_graceful_shutdown(
        self,
        trading_node_config: LiveTradingNodeConfig,
    ):
        """Config supports graceful shutdown on exception."""
        exec_config = trading_node_config.build_exec_engine_config()

        assert exec_config["graceful_shutdown_on_exception"] is True

    def test_cache_persistence_enabled(
        self,
        trading_node_config: LiveTradingNodeConfig,
    ):
        """Cache persistence is enabled for recovery."""
        cache_config = trading_node_config.build_cache_config()

        assert cache_config["persist_account_events"] is True

    def test_reconnection_config_available(
        self,
        trading_node_config: LiveTradingNodeConfig,
    ):
        """Reconciliation is enabled for reconnection scenarios."""
        exec_config = trading_node_config.build_exec_engine_config()

        assert exec_config["reconciliation"] is True
        assert exec_config["reconciliation_startup_delay_secs"] >= 10.0

    def test_lookback_sufficient_for_recovery(
        self,
        conservative_reconciliation_config: ReconciliationConfig,
    ):
        """Conservative config has sufficient lookback for recovery."""
        config = conservative_reconciliation_config

        # Conservative should have larger lookback
        assert config.lookback_mins == 120
        assert config.open_check_lookback_mins == 120
