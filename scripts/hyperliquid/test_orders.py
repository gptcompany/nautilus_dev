#!/usr/bin/env python3
"""Test order execution on Hyperliquid testnet (Spec 021 - US3).

This script tests various order types on the Hyperliquid testnet:
- MARKET orders
- LIMIT orders
- STOP_MARKET orders
- STOP_LIMIT orders

IMPORTANT: Requires testnet credentials set in environment:
    export HYPERLIQUID_TESTNET_PK="0x..."

Usage:
    python scripts/hyperliquid/test_orders.py --order-type market
    python scripts/hyperliquid/test_orders.py --order-type limit --price 95000
    python scripts/hyperliquid/test_orders.py --order-type stop_market --trigger 94000

Example:
    # Test a small MARKET buy order
    python scripts/hyperliquid/test_orders.py --order-type market --size 0.001 --side buy
"""

import argparse
import os
import time
from datetime import datetime
from decimal import Decimal

from nautilus_trader.common.enums import LogLevel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.events import OrderFilled, OrderRejected, OrderAccepted
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.objects import Price, Quantity
from nautilus_trader.trading.strategy import Strategy

from configs.hyperliquid.testnet import create_testnet_trading_node


class OrderTestStrategy(Strategy):
    """Strategy for testing order execution on testnet."""

    def __init__(
        self,
        instrument_id_str: str,
        order_type: str,
        side: str,
        size: float,
        price: float | None = None,
        trigger_price: float | None = None,
        reduce_only: bool = False,
    ):
        super().__init__()
        self.instrument_id_str = instrument_id_str
        self.order_type = order_type
        self.side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
        self.size = Decimal(str(size))
        self.price = Price.from_str(str(price)) if price else None
        self.trigger_price = (
            Price.from_str(str(trigger_price)) if trigger_price else None
        )
        self.reduce_only = reduce_only

        self.order_submitted = False
        self.order_result: str | None = None

    def on_start(self) -> None:
        """Subscribe to data and submit test order."""
        instrument_id = InstrumentId.from_str(self.instrument_id_str)

        # Subscribe to quotes to get current price
        self.subscribe_quote_ticks(instrument_id)

        self.log.info(
            f"Order test started: {self.order_type.upper()} {self.side.name} "
            f"{self.size} @ {self.price or 'MARKET'}"
        )

    def on_quote_tick(self, tick) -> None:
        """Submit order after receiving first quote."""
        if self.order_submitted:
            return

        self.order_submitted = True
        instrument_id = InstrumentId.from_str(self.instrument_id_str)
        quantity = Quantity.from_str(str(self.size))

        self.log.info(f"Current market: bid={tick.bid_price}, ask={tick.ask_price}")

        try:
            if self.order_type == "market":
                self._submit_market_order(instrument_id, quantity)
            elif self.order_type == "limit":
                self._submit_limit_order(instrument_id, quantity)
            elif self.order_type == "stop_market":
                self._submit_stop_market_order(instrument_id, quantity)
            elif self.order_type == "stop_limit":
                self._submit_stop_limit_order(instrument_id, quantity)
            else:
                self.log.error(f"Unknown order type: {self.order_type}")
                self.stop()
        except Exception as e:
            self.log.error(f"Order submission failed: {e}")
            self.order_result = f"ERROR: {e}"
            self.stop()

    def _submit_market_order(
        self, instrument_id: InstrumentId, quantity: Quantity
    ) -> None:
        """Submit a MARKET order."""
        order = self.order_factory.market(
            instrument_id=instrument_id,
            order_side=self.side,
            quantity=quantity,
        )
        self.submit_order(order)
        self.log.info(f"MARKET order submitted: {order.client_order_id}")

    def _submit_limit_order(
        self, instrument_id: InstrumentId, quantity: Quantity
    ) -> None:
        """Submit a LIMIT order."""
        if self.price is None:
            raise ValueError("Limit order requires --price")

        order = self.order_factory.limit(
            instrument_id=instrument_id,
            order_side=self.side,
            quantity=quantity,
            price=self.price,
            time_in_force=TimeInForce.GTC,
            post_only=True,
        )
        self.submit_order(order)
        self.log.info(f"LIMIT order submitted: {order.client_order_id} @ {self.price}")

    def _submit_stop_market_order(
        self, instrument_id: InstrumentId, quantity: Quantity
    ) -> None:
        """Submit a STOP_MARKET order."""
        if self.trigger_price is None:
            raise ValueError("Stop market order requires --trigger")

        order = self.order_factory.stop_market(
            instrument_id=instrument_id,
            order_side=self.side,
            quantity=quantity,
            trigger_price=self.trigger_price,
            reduce_only=self.reduce_only,
        )
        self.submit_order(order)
        self.log.info(
            f"STOP_MARKET order submitted: {order.client_order_id} "
            f"trigger={self.trigger_price} reduce_only={self.reduce_only}"
        )

    def _submit_stop_limit_order(
        self, instrument_id: InstrumentId, quantity: Quantity
    ) -> None:
        """Submit a STOP_LIMIT order."""
        if self.trigger_price is None:
            raise ValueError("Stop limit order requires --trigger")
        if self.price is None:
            raise ValueError("Stop limit order requires --price")

        order = self.order_factory.stop_limit(
            instrument_id=instrument_id,
            order_side=self.side,
            quantity=quantity,
            price=self.price,
            trigger_price=self.trigger_price,
            time_in_force=TimeInForce.GTC,
            reduce_only=self.reduce_only,
        )
        self.submit_order(order)
        self.log.info(
            f"STOP_LIMIT order submitted: {order.client_order_id} "
            f"trigger={self.trigger_price} limit={self.price}"
        )

    def on_event(self, event) -> None:
        """Handle order events."""
        if isinstance(event, OrderAccepted):
            self.log.info(f"Order ACCEPTED: {event.client_order_id}")
            self.order_result = "ACCEPTED"

        elif isinstance(event, OrderFilled):
            latency_ns = time.time_ns() - event.ts_event
            latency_ms = latency_ns / 1_000_000
            self.log.info(
                f"Order FILLED: {event.client_order_id} "
                f"price={event.last_px} qty={event.last_qty} "
                f"latency={latency_ms:.1f}ms"
            )
            self.order_result = f"FILLED @ {event.last_px}"
            # Stop after fill
            self.stop()

        elif isinstance(event, OrderRejected):
            self.log.error(
                f"Order REJECTED: {event.client_order_id} reason={event.reason}"
            )
            self.order_result = f"REJECTED: {event.reason}"
            self.stop()

    def on_stop(self) -> None:
        """Log final result."""
        self.log.info(f"Test complete. Result: {self.order_result}")


def main():
    """Run order test script."""
    parser = argparse.ArgumentParser(
        description="Test order execution on Hyperliquid testnet"
    )
    parser.add_argument(
        "--order-type",
        type=str,
        required=True,
        choices=["market", "limit", "stop_market", "stop_limit"],
        help="Type of order to submit",
    )
    parser.add_argument(
        "--instrument",
        type=str,
        default="BTC-USD-PERP.HYPERLIQUID",
        help="Instrument to trade (default: BTC-USD-PERP.HYPERLIQUID)",
    )
    parser.add_argument(
        "--side",
        type=str,
        default="buy",
        choices=["buy", "sell"],
        help="Order side (default: buy)",
    )
    parser.add_argument(
        "--size",
        type=float,
        default=0.001,
        help="Order size (default: 0.001 - minimum for BTC)",
    )
    parser.add_argument(
        "--price",
        type=float,
        default=None,
        help="Limit price (required for limit and stop_limit orders)",
    )
    parser.add_argument(
        "--trigger",
        type=float,
        default=None,
        help="Trigger price (required for stop_market and stop_limit orders)",
    )
    parser.add_argument(
        "--reduce-only",
        action="store_true",
        help="Set reduce_only=True for stop orders",
    )
    args = parser.parse_args()

    # Check for testnet credentials
    if not os.environ.get("HYPERLIQUID_TESTNET_PK"):
        print("ERROR: HYPERLIQUID_TESTNET_PK environment variable not set")
        print("Set it with: export HYPERLIQUID_TESTNET_PK='0x...'")
        return

    print(f"[{datetime.now()}] Testing Hyperliquid order execution")
    print(f"  Order Type: {args.order_type.upper()}")
    print(f"  Instrument: {args.instrument}")
    print(f"  Side: {args.side.upper()}")
    print(f"  Size: {args.size}")
    print(f"  Price: {args.price}")
    print(f"  Trigger: {args.trigger}")
    print(f"  Reduce Only: {args.reduce_only}")

    # Create base testnet node configuration
    base_config = create_testnet_trading_node(
        trader_id="TRADER-HL-ORDER-TEST",
        instruments=[args.instrument],
    )

    # Reconstruct config with logging (TradingNodeConfig is frozen)
    from nautilus_trader.config import TradingNodeConfig

    config = TradingNodeConfig(
        trader_id=base_config.trader_id,
        data_clients=base_config.data_clients,
        exec_clients=base_config.exec_clients,
        logging=LoggingConfig(log_level=LogLevel.INFO),
    )

    # Create node
    node = TradingNode(config=config)

    # Add test strategy
    strategy = OrderTestStrategy(
        instrument_id_str=args.instrument,
        order_type=args.order_type,
        side=args.side,
        size=args.size,
        price=args.price,
        trigger_price=args.trigger,
        reduce_only=args.reduce_only,
    )
    node.trader.add_strategy(strategy)

    # Run node
    try:
        node.run()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    finally:
        print(f"[{datetime.now()}] Order test complete")
        if strategy.order_result:
            print(f"Result: {strategy.order_result}")


if __name__ == "__main__":
    main()
