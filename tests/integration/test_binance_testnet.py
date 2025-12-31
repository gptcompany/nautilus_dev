"""
Integration Tests for Binance Testnet (Spec 015 Phase 8).

These tests validate the complete order lifecycle on Binance testnet.
They require valid testnet API credentials set in environment variables.

Environment Variables Required:
- BINANCE_TESTNET_API_KEY: Testnet API key
- BINANCE_TESTNET_API_SECRET: Testnet API secret

To run these tests:
    pytest tests/integration/test_binance_testnet.py -v -m integration

Notes
-----
- Tests are skipped if credentials are not set
- Testnet may have occasional availability issues
- Order execution latency tests may be flaky due to network conditions
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add project root to sys.path for imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import pytest

# Skip all tests if testnet credentials not available
TESTNET_API_KEY = os.environ.get("BINANCE_TESTNET_API_KEY")
TESTNET_API_SECRET = os.environ.get("BINANCE_TESTNET_API_SECRET")
SKIP_REASON = "Binance testnet credentials not set"


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        not (TESTNET_API_KEY and TESTNET_API_SECRET),
        reason=SKIP_REASON,
    ),
]


@pytest.fixture
def testnet_credentials():
    """Create testnet credentials from environment."""
    from config.models import BinanceCredentials

    return BinanceCredentials(
        api_key=TESTNET_API_KEY,
        api_secret=TESTNET_API_SECRET,
        account_type="USDT_FUTURES",
        testnet=True,
    )


@pytest.fixture
def binance_exec_config(testnet_credentials):
    """Create Binance exec client config for testnet."""
    from config.clients.binance import build_binance_exec_client_config

    return build_binance_exec_client_config(
        testnet_credentials,
        max_retries=3,
        retry_delay_initial_ms=500,
        retry_delay_max_ms=5000,
    )


class TestBinanceTestnetConnection:
    """Tests for Binance testnet connectivity."""

    def test_config_creation(self, binance_exec_config):
        """Config should be created successfully for testnet."""
        assert binance_exec_config is not None
        assert binance_exec_config.testnet is True

    def test_account_type_usdt_futures(self, binance_exec_config):
        """Config should be set for USDT futures."""
        from nautilus_trader.adapters.binance.common.enums import BinanceAccountType

        assert binance_exec_config.account_type == BinanceAccountType.USDT_FUTURES

    def test_reduce_only_enabled(self, binance_exec_config):
        """Config should have reduce_only enabled for NETTING mode."""
        assert binance_exec_config.use_reduce_only is True


class TestOrderHelpers:
    """Tests for order helper functions in testnet context."""

    @pytest.fixture
    def order_factory(self):
        """Create order factory for testing."""
        from nautilus_trader.common.component import TestClock
        from nautilus_trader.common.factories import OrderFactory
        from nautilus_trader.model.identifiers import StrategyId, TraderId

        clock = TestClock()
        return OrderFactory(
            trader_id=TraderId("TESTER-001"),
            strategy_id=StrategyId("TestStrategy-001"),
            clock=clock,
        )

    @pytest.fixture
    def btc_instrument_id(self):
        """Create BTCUSDT perpetual instrument ID."""
        from nautilus_trader.model.identifiers import InstrumentId

        return InstrumentId.from_str("BTCUSDT-PERP.BINANCE")

    def test_create_market_order(self, order_factory, btc_instrument_id):
        """Market order helper should create valid order."""
        from nautilus_trader.model.enums import OrderSide
        from nautilus_trader.model.objects import Quantity

        from config import create_market_order

        order = create_market_order(
            order_factory,
            btc_instrument_id,
            OrderSide.BUY,
            Quantity.from_str("0.001"),
        )
        assert order is not None
        assert order.instrument_id == btc_instrument_id

    def test_create_limit_order(self, order_factory, btc_instrument_id):
        """Limit order helper should create valid order."""
        from nautilus_trader.model.enums import OrderSide
        from nautilus_trader.model.objects import Price, Quantity

        from config import create_limit_order

        order = create_limit_order(
            order_factory,
            btc_instrument_id,
            OrderSide.SELL,
            Quantity.from_str("0.001"),
            Price.from_str("100000.00"),
            post_only=True,
        )
        assert order is not None
        assert order.is_post_only is True

    def test_create_stop_market_order(self, order_factory, btc_instrument_id):
        """Stop-market order helper should create valid order (Algo API)."""
        from nautilus_trader.model.enums import OrderSide
        from nautilus_trader.model.objects import Price, Quantity

        from config import create_stop_market_order

        order = create_stop_market_order(
            order_factory,
            btc_instrument_id,
            OrderSide.SELL,
            Quantity.from_str("0.001"),
            Price.from_str("40000.00"),
            reduce_only=True,
        )
        assert order is not None
        assert order.is_reduce_only is True


class TestExternalClaims:
    """Tests for external order claims helper."""

    def test_create_claims_for_binance(self):
        """External claims should create valid InstrumentId list."""
        from nautilus_trader.model.identifiers import InstrumentId

        from config import create_external_claims

        claims = create_external_claims(
            [
                "BTCUSDT-PERP.BINANCE",
                "ETHUSDT-PERP.BINANCE",
            ]
        )
        assert len(claims) == 2
        assert all(isinstance(c, InstrumentId) for c in claims)


# =============================================================================
# Live Order Tests (Require Running TradingNode)
# =============================================================================
# Note: The following tests are marked as expected to be skipped
# because they require a fully running TradingNode with live connection.
# They serve as documentation for manual testing procedures.


@pytest.mark.skip(reason="Requires live TradingNode connection")
class TestLiveOrderExecution:
    """
    Live order execution tests (manual testing reference).

    These tests document the expected behavior for live order testing
    on Binance testnet. Run manually with a configured TradingNode.
    """

    def test_market_order_round_trip(self):
        """
        MARKET order round-trip test.

        Expected:
        1. Submit MARKET BUY order
        2. Verify fill event received
        3. Check latency < 100ms
        4. Submit MARKET SELL to close
        5. Verify position closed
        """
        pass

    def test_limit_order_lifecycle(self):
        """
        LIMIT order lifecycle test.

        Expected:
        1. Submit LIMIT order far from market
        2. Verify ACCEPTED state
        3. Cancel order
        4. Verify CANCELED state
        """
        pass

    def test_stop_market_order(self):
        """
        STOP_MARKET order test (Algo Order API).

        Expected:
        1. Submit STOP_MARKET order
        2. Verify order created via Algo API
        3. Cancel order
        4. Verify cancellation
        """
        pass

    def test_fill_notification_latency(self):
        """
        Fill notification latency test.

        Expected:
        - Fill notification received < 50ms after exchange fill
        """
        pass

    def test_websocket_reconnection(self):
        """
        WebSocket reconnection test.

        Expected:
        1. Establish connection
        2. Simulate network interruption
        3. Verify automatic reconnection
        4. Verify order state consistency
        """
        pass
