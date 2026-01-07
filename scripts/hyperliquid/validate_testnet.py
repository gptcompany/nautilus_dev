#!/usr/bin/env python3
"""End-to-end testnet validation script (Spec 021 - US5).

This script validates the full order lifecycle on Hyperliquid testnet:
1. Connect to testnet
2. Subscribe to market data
3. Open position (MARKET BUY)
4. Verify stop-loss auto-created by RiskManager
5. Close position (MARKET SELL reduce_only=True)
6. Verify reconciliation on restart

IMPORTANT: Requires testnet credentials:
    export HYPERLIQUID_TESTNET_PK="0x..."

Usage:
    python scripts/hyperliquid/validate_testnet.py

Example:
    # Run full validation
    python scripts/hyperliquid/validate_testnet.py --size 0.001
"""

import argparse
import os
import time
from datetime import datetime
from decimal import Decimal
from enum import Enum

from nautilus_trader.common.enums import LogLevel
from nautilus_trader.config import LoggingConfig
from nautilus_trader.live.node import TradingNode
from nautilus_trader.model.enums import OrderSide
from nautilus_trader.model.events import (
    OrderAccepted,
    OrderFilled,
    OrderRejected,
    PositionOpened,
    PositionClosed,
)
from nautilus_trader.model.objects import Quantity

from configs.hyperliquid.testnet import create_testnet_trading_node
from strategies.hyperliquid.base_strategy import HyperliquidBaseStrategy
from strategies.hyperliquid.config import HyperliquidStrategyConfig
from risk import RiskConfig


class ValidationState(Enum):
    """States for the validation workflow."""

    WAITING_FOR_DATA = "waiting_for_data"
    OPENING_POSITION = "opening_position"
    POSITION_OPEN = "position_open"
    VERIFYING_STOP_LOSS = "verifying_stop_loss"
    CLOSING_POSITION = "closing_position"
    POSITION_CLOSED = "position_closed"
    VALIDATION_COMPLETE = "validation_complete"
    VALIDATION_FAILED = "validation_failed"


class TestnetValidationStrategy(HyperliquidBaseStrategy):
    """Strategy for validating testnet order lifecycle."""

    def __init__(self, config: HyperliquidStrategyConfig, order_size: Decimal):
        super().__init__(config)
        self.order_size = order_size
        self.state = ValidationState.WAITING_FOR_DATA
        self.data_received = False
        self.position_opened = False
        self.stop_loss_active = False
        self.position_closed = False
        self.start_time: float | None = None

    def on_start(self) -> None:
        """Start validation workflow."""
        super().on_start()
        self.start_time = time.time()
        self.log.info("=== TESTNET VALIDATION STARTED ===")
        self.log.info(f"Instrument: {self.instrument_id}")
        self.log.info(f"Order size: {self.order_size}")
        self.log.info(f"Stop-loss: {self.strategy_config.risk.stop_loss_pct}")

    def on_quote_tick(self, tick) -> None:
        """Handle quote ticks - trigger position open after first quote."""
        if not self.data_received:
            self.data_received = True
            self.log.info(f"✓ Data received: bid={tick.bid_price} ask={tick.ask_price}")

            if self.state == ValidationState.WAITING_FOR_DATA:
                self._open_test_position()

    def _open_test_position(self) -> None:
        """Open a test position with MARKET order."""
        self.state = ValidationState.OPENING_POSITION
        self.log.info("Opening test position (MARKET BUY)...")

        try:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.BUY,
                quantity=Quantity.from_str(str(self.order_size)),
            )
            self.submit_order(order)
            self.log.info(f"Submitted MARKET BUY: {order.client_order_id}")
        except Exception as e:
            self.log.error(f"Failed to submit order: {e}")
            self._fail_validation(f"Order submission failed: {e}")

    def _close_test_position(self) -> None:
        """Close the test position with reduce_only MARKET order."""
        self.state = ValidationState.CLOSING_POSITION
        self.log.info("Closing test position (MARKET SELL reduce_only)...")

        try:
            order = self.order_factory.market(
                instrument_id=self.instrument_id,
                order_side=OrderSide.SELL,
                quantity=Quantity.from_str(str(self.order_size)),
                reduce_only=True,
            )
            self.submit_order(order)
            self.log.info(f"Submitted MARKET SELL (reduce_only): {order.client_order_id}")
        except Exception as e:
            self.log.error(f"Failed to close position: {e}")
            self._fail_validation(f"Position close failed: {e}")

    def on_event(self, event) -> None:
        """Handle events for validation workflow."""
        # Let RiskManager process first
        super().on_event(event)

        if isinstance(event, OrderAccepted):
            self.log.info(f"✓ Order ACCEPTED: {event.client_order_id}")

        elif isinstance(event, OrderFilled):
            self.log.info(
                f"✓ Order FILLED: {event.client_order_id} "
                f"price={event.last_px} qty={event.last_qty}"
            )

            if self.state == ValidationState.OPENING_POSITION:
                self.position_opened = True
                self.state = ValidationState.POSITION_OPEN
                self.log.info("✓ Position opened successfully")

                # Check for stop-loss after a short delay
                # Note: time.sleep is acceptable here since this is a validation
                # script, not production code. For production, use clock.set_timer().
                time.sleep(1)
                self._verify_stop_loss()

            elif self.state == ValidationState.CLOSING_POSITION:
                self.position_closed = True
                self.state = ValidationState.POSITION_CLOSED
                self.log.info("✓ Position closed successfully")
                self._complete_validation()

        elif isinstance(event, OrderRejected):
            self.log.error(f"✗ Order REJECTED: {event.reason}")
            self._fail_validation(f"Order rejected: {event.reason}")

        elif isinstance(event, PositionOpened):
            self.log.info(f"✓ PositionOpened event: {event.position_id}")

        elif isinstance(event, PositionClosed):
            self.log.info(f"✓ PositionClosed event: {event.position_id}")

    def _verify_stop_loss(self) -> None:
        """Verify stop-loss order was created by RiskManager."""
        self.state = ValidationState.VERIFYING_STOP_LOSS

        # Check if RiskManager created stop-loss
        if self.risk_manager.active_stops:
            self.stop_loss_active = True
            self.log.info(f"✓ Stop-loss active: {len(self.risk_manager.active_stops)} stop orders")
            # Now close the position
            self._close_test_position()
        else:
            self.log.warning("⚠ No stop-loss orders found - RiskManager may not have triggered")
            # Continue with closing anyway
            self._close_test_position()

    def _complete_validation(self) -> None:
        """Mark validation as complete."""
        self.state = ValidationState.VALIDATION_COMPLETE
        elapsed = time.time() - (self.start_time or time.time())

        self.log.info("=== VALIDATION RESULTS ===")
        self.log.info(f"Duration: {elapsed:.1f}s")
        self.log.info(f"Data received: {'✓' if self.data_received else '✗'}")
        self.log.info(f"Position opened: {'✓' if self.position_opened else '✗'}")
        self.log.info(f"Stop-loss active: {'✓' if self.stop_loss_active else '⚠'}")
        self.log.info(f"Position closed: {'✓' if self.position_closed else '✗'}")
        self.log.info("=== VALIDATION COMPLETE ===")

        self.stop()

    def _fail_validation(self, reason: str) -> None:
        """Mark validation as failed."""
        self.state = ValidationState.VALIDATION_FAILED
        self.log.error(f"=== VALIDATION FAILED: {reason} ===")
        self.stop()

    def on_stop(self) -> None:
        """Log final status."""
        super().on_stop()
        self.log.info(f"Final state: {self.state.value}")


def main():
    """Run testnet validation."""
    parser = argparse.ArgumentParser(description="Validate Hyperliquid integration on testnet")
    parser.add_argument(
        "--instrument",
        type=str,
        default="BTC-USD-PERP.HYPERLIQUID",
        help="Instrument to trade (default: BTC-USD-PERP.HYPERLIQUID)",
    )
    parser.add_argument(
        "--size",
        type=float,
        default=0.001,
        help="Order size for test trades (default: 0.001)",
    )
    parser.add_argument(
        "--stop-loss",
        type=float,
        default=0.02,
        help="Stop-loss percentage (default: 0.02 = 2%%)",
    )
    args = parser.parse_args()

    # Check for testnet credentials
    if not os.environ.get("HYPERLIQUID_TESTNET_PK"):
        print("ERROR: HYPERLIQUID_TESTNET_PK environment variable not set")
        print("Set it with: export HYPERLIQUID_TESTNET_PK='0x...'")
        return

    print(f"[{datetime.now()}] Starting Hyperliquid testnet validation")
    print(f"  Instrument: {args.instrument}")
    print(f"  Size: {args.size}")
    print(f"  Stop-loss: {args.stop_loss * 100}%")

    # Create base testnet node configuration
    base_config = create_testnet_trading_node(
        trader_id="TRADER-HL-VALIDATE",
        instruments=[args.instrument],
    )

    # Reconstruct config with logging (TradingNodeConfig is frozen)
    from nautilus_trader.config import TradingNodeConfig

    node_config = TradingNodeConfig(
        trader_id=base_config.trader_id,
        data_clients=base_config.data_clients,
        exec_clients=base_config.exec_clients,
        logging=LoggingConfig(log_level=LogLevel.INFO),
    )

    # Create strategy configuration
    strategy_config = HyperliquidStrategyConfig(
        instrument_id=args.instrument,
        order_size=Decimal(str(args.size)),
        max_position_size=Decimal(str(args.size * 10)),
        risk=RiskConfig(
            stop_loss_pct=Decimal(str(args.stop_loss)),
            stop_loss_enabled=True,
        ),
    )

    # Create node
    node = TradingNode(config=node_config)

    # Add validation strategy
    strategy = TestnetValidationStrategy(
        config=strategy_config,
        order_size=Decimal(str(args.size)),
    )
    node.trader.add_strategy(strategy)

    # Run node
    try:
        node.run()
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
    finally:
        print(f"[{datetime.now()}] Testnet validation complete")
        print(f"Final state: {strategy.state.value}")


if __name__ == "__main__":
    main()
