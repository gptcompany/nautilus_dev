"""
Risk Manager Implementation.

Manages automatic stop-loss generation and position limit validation
for NautilusTrader strategies.

This implementation uses a minimal event-driven approach with simple
if/elif routing for optimal testability and compatibility with mocks.
"""

from decimal import Decimal
from typing import TYPE_CHECKING

from nautilus_trader.model.enums import OrderSide, PositionSide
from nautilus_trader.model.events import PositionChanged, PositionClosed, PositionOpened
from nautilus_trader.model.identifiers import ClientOrderId, PositionId
from nautilus_trader.model.objects import Price

from risk.config import RiskConfig, StopLossType

if TYPE_CHECKING:
    from nautilus_trader.model.events import Event
    from nautilus_trader.model.orders import Order
    from nautilus_trader.model.position import Position
    from nautilus_trader.trading.strategy import Strategy


class RiskManager:
    """
    Manages stop-loss and position limits for strategies.

    Manages stop-loss and position limits for strategies.

    The RiskManager is responsible for:
    1. Generating stop-loss orders when positions open
    2. Canceling stop-loss orders when positions close
    3. Updating trailing stops on position changes
    4. Validating orders against position limits
    """

    def __init__(self, config: RiskConfig, strategy: "Strategy") -> None:
        self._config = config
        self._strategy = strategy
        self._active_stops: dict[PositionId, ClientOrderId] = {}

    @property
    def config(self) -> RiskConfig:
        return self._config

    @property
    def active_stops(self) -> dict[PositionId, ClientOrderId]:
        return self._active_stops

    def handle_event(self, event: "Event") -> None:
        """Route events with simple if/elif chain."""
        if isinstance(event, PositionOpened):
            self._on_position_opened(event)
        elif isinstance(event, PositionClosed):
            self._on_position_closed(event)
        elif isinstance(event, PositionChanged):
            self._on_position_changed(event)

    def validate_order(self, order: "Order") -> bool:
        """Pre-flight check against position limits."""
        if (
            self._config.max_position_size is None
            and self._config.max_total_exposure is None
        ):
            return True

        instrument_id_str = str(order.instrument_id)

        # Check per-instrument limit
        if self._config.max_position_size is not None:
            max_size = self._config.max_position_size.get(instrument_id_str)
            if max_size is not None:
                current_size = self._get_current_position_size(order.instrument_id)
                order_qty = float(order.quantity)

                if order.side == OrderSide.SELL:
                    pass  # Selling reduces risk
                else:
                    projected = current_size + order_qty
                    if projected > float(max_size):
                        return False

        # Check total exposure limit
        if self._config.max_total_exposure is not None:
            current_exposure = self._get_total_exposure()
            order_notional = self._estimate_order_notional(order)
            projected_exposure = current_exposure + order_notional

            if projected_exposure > float(self._config.max_total_exposure):
                return False

        return True

    def _on_position_opened(self, event: PositionOpened) -> None:
        if not self._config.stop_loss_enabled:
            return

        position = self._strategy.cache.position(event.position_id)
        if position is None:
            return

        stop_price = self._calculate_stop_price(position)
        stop_order = self._create_stop_order(position, stop_price)
        self._strategy.submit_order(stop_order)
        self._active_stops[position.id] = stop_order.client_order_id

    def _on_position_closed(self, event: PositionClosed) -> None:
        position_id = event.position_id
        if position_id not in self._active_stops:
            return

        stop_order_id = self._active_stops[position_id]
        self._strategy.cancel_order(stop_order_id)
        del self._active_stops[position_id]

    def _on_position_changed(self, event: PositionChanged) -> None:
        """
        Update trailing stop when position changes.

        Note: MVP implementation uses avg_px_open as reference price.
        Full trailing stop would track high watermark for LONG positions.
        """
        if not self._config.trailing_stop:
            return

        position_id = event.position_id
        if position_id not in self._active_stops:
            return

        position = self._strategy.cache.position(position_id)
        if position is None:
            return

        old_stop_id = self._active_stops[position_id]

        # Create new stop before canceling old one to maintain protection
        try:
            new_stop_price = self._calculate_trailing_stop_price(position)
            new_stop_order = self._create_stop_order(position, new_stop_price)
            self._strategy.submit_order(new_stop_order)
            self._active_stops[position_id] = new_stop_order.client_order_id
            # Only cancel old stop after new one is submitted
            self._strategy.cancel_order(old_stop_id)
        except Exception:
            # If new stop fails, keep old stop active for protection
            pass

    def _calculate_stop_price(self, position: "Position") -> Price:
        """
        Calculate stop price based on position and config.

        For LONG: stop_price = entry_price * (1 - stop_loss_pct)
        For SHORT: stop_price = entry_price * (1 + stop_loss_pct)
        """
        entry_price = Decimal(str(position.avg_px_open))
        stop_loss_pct = self._config.stop_loss_pct

        if position.side == PositionSide.LONG:
            stop_price_decimal = entry_price * (1 - stop_loss_pct)
        else:
            stop_price_decimal = entry_price * (1 + stop_loss_pct)

        instrument = self._strategy.cache.instrument(position.instrument_id)
        if instrument is not None:
            return instrument.make_price(stop_price_decimal)

        return Price.from_str(str(stop_price_decimal))

    def _calculate_trailing_stop_price(self, position: "Position") -> Price:
        current_price = Decimal(str(position.avg_px_open))
        trailing_pct = self._config.trailing_distance_pct

        if position.side == PositionSide.LONG:
            stop_price_decimal = current_price * (1 - trailing_pct)
        else:
            stop_price_decimal = current_price * (1 + trailing_pct)

        instrument = self._strategy.cache.instrument(position.instrument_id)
        if instrument is not None:
            return instrument.make_price(stop_price_decimal)

        return Price.from_str(str(stop_price_decimal))

    def _create_stop_order(self, position: "Position", stop_price: Price) -> "Order":
        """Create stop order with reduce_only=True."""
        order_side = (
            OrderSide.SELL if position.side == PositionSide.LONG else OrderSide.BUY
        )
        quantity = position.quantity

        if self._config.stop_loss_type == StopLossType.LIMIT:
            return self._strategy.order_factory.stop_limit(
                instrument_id=position.instrument_id,
                order_side=order_side,
                quantity=quantity,
                trigger_price=stop_price,
                price=stop_price,
                reduce_only=True,
            )
        else:
            return self._strategy.order_factory.stop_market(
                instrument_id=position.instrument_id,
                order_side=order_side,
                quantity=quantity,
                trigger_price=stop_price,
                reduce_only=True,
            )

    def _get_current_position_size(self, instrument_id) -> float:
        positions = self._strategy.cache.positions_open()
        for pos in positions:
            if pos.instrument_id == instrument_id:
                return abs(float(pos.quantity))
        return 0.0

    def _get_total_exposure(self) -> float:
        net_exposure = self._strategy.portfolio.net_exposure()
        if net_exposure is not None:
            return float(net_exposure)
        return 0.0

    def _estimate_order_notional(self, order: "Order") -> float:
        """
        Estimate order notional value.

        Note: MVP uses simplified calculation. Production would query
        current market price from cache or data provider.
        """
        # TODO: Get actual price from cache/market data
        return float(order.quantity) * 50000.0
