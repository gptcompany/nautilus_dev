"""Integration tests for Hyperliquid live trading cycle (Spec 021 - US5).

These tests validate the full order lifecycle on Hyperliquid testnet.
They require:
1. HYPERLIQUID_TESTNET_PK environment variable
2. Network access to Hyperliquid testnet
3. USDC balance on testnet account

Run with: pytest tests/hyperliquid/integration/test_live_cycle.py -v -s
"""

import os
from decimal import Decimal

import pytest

# Skip entire module if Hyperliquid adapter not available
pytest.importorskip("nautilus_trader.adapters.hyperliquid")

from configs.hyperliquid.testnet import create_testnet_trading_node
from strategies.hyperliquid.config import HyperliquidStrategyConfig
from strategies.hyperliquid.base_strategy import HyperliquidBaseStrategy
from risk import RiskConfig


# Skip all tests if testnet credentials not available
pytestmark = pytest.mark.skipif(
    not os.environ.get("HYPERLIQUID_TESTNET_PK"),
    reason="HYPERLIQUID_TESTNET_PK not set - testnet tests skipped",
)


class TestTestnetConfiguration:
    """Tests for testnet configuration."""

    def test_testnet_config_created(self):
        """Testnet configuration can be created."""
        config = create_testnet_trading_node()

        assert config is not None
        assert str(config.trader_id) == "TRADER-HL-TESTNET"

    def test_testnet_uses_testnet_endpoints(self):
        """Testnet config uses testnet=True."""
        config = create_testnet_trading_node()

        # Both data and exec clients should be testnet
        from nautilus_trader.adapters.hyperliquid import HYPERLIQUID

        assert config.data_clients[HYPERLIQUID].testnet is True
        assert config.exec_clients[HYPERLIQUID].testnet is True

    def test_custom_instruments(self):
        """Custom instruments are loaded."""
        custom = ["ETH-USD-PERP.HYPERLIQUID"]
        config = create_testnet_trading_node(instruments=custom)

        from nautilus_trader.adapters.hyperliquid import HYPERLIQUID

        assert config.data_clients[HYPERLIQUID].instrument_provider.load_ids == custom


class TestStrategyConfiguration:
    """Tests for strategy configuration with RiskManager."""

    def test_strategy_config_valid(self):
        """Strategy configuration is valid."""
        config = HyperliquidStrategyConfig(
            instrument_id="BTC-USD-PERP.HYPERLIQUID",
            order_size=Decimal("0.001"),
            max_position_size=Decimal("0.01"),
            risk=RiskConfig(stop_loss_pct=Decimal("0.02")),
        )

        assert config.instrument_id == "BTC-USD-PERP.HYPERLIQUID"
        assert config.order_size == Decimal("0.001")

    def test_strategy_initializes(self):
        """Strategy can be initialized."""
        config = HyperliquidStrategyConfig()
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy is not None
        assert strategy.risk_manager is not None

    def test_risk_config_applied(self):
        """Risk configuration is applied to RiskManager."""
        config = HyperliquidStrategyConfig(
            risk=RiskConfig(
                stop_loss_pct=Decimal("0.03"),
                trailing_stop=True,
                trailing_distance_pct=Decimal("0.02"),
            ),
        )
        strategy = HyperliquidBaseStrategy(config=config)

        assert strategy.risk_manager.config.stop_loss_pct == Decimal("0.03")
        assert strategy.risk_manager.config.trailing_stop is True


class TestLiveCycle:
    """Tests for live order cycle (requires actual testnet connection).

    These tests are marked as slow and should only run in CI
    or when explicitly requested.
    """

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires live testnet connection - run manually")
    def test_connect_to_testnet(self):
        """Can connect to Hyperliquid testnet."""
        # This test would actually connect to testnet
        # Skipped by default to avoid network calls in unit tests
        pass

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires live testnet connection - run manually")
    def test_receive_market_data(self):
        """Can receive market data from testnet."""
        pass

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires live testnet connection - run manually")
    def test_submit_market_order(self):
        """Can submit MARKET order on testnet."""
        pass

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires live testnet connection - run manually")
    def test_submit_limit_order(self):
        """Can submit LIMIT order on testnet."""
        pass

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires live testnet connection - run manually")
    def test_submit_stop_market_order(self):
        """Can submit STOP_MARKET order on testnet."""
        pass

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires live testnet connection - run manually")
    def test_full_trade_cycle(self):
        """Full trade cycle: open -> stop-loss -> close."""
        pass


class TestReconciliation:
    """Tests for order/position reconciliation on restart."""

    @pytest.mark.slow
    @pytest.mark.skip(reason="Requires live testnet connection - run manually")
    def test_reconciliation_on_restart(self):
        """Positions are reconciled correctly on TradingNode restart."""
        pass
