"""
Liquidation HeatMap Strategy for NautilusTrader.

Converted from: Liquidation HeatMap [BigBeluga]
Source: https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/
License: CC BY-NC-SA 4.0

Trading Logic:
- Identifies liquidation zones (potential stop-loss clusters)
- Trades reversals when price approaches high-volume liquidation zones
- Uses ATR for zone width and dynamic stop placement
"""

from decimal import Decimal
from typing import Optional

from nautilus_trader.config import StrategyConfig
from nautilus_trader.model.data import Bar, BarType
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.trading.strategy import Strategy

from .liquidation_zone_indicator import LiquidationZoneIndicator, LiquidationZone


class LiquidationHeatMapConfig(StrategyConfig, frozen=True):
    """Configuration for LiquidationHeatMap strategy."""

    instrument_id: str
    bar_type: str

    # Indicator settings (from Pine Script)
    atr_period: int = 200
    pivot_lookback: int = 2
    max_zones: int = 500
    atr_multiplier: float = 0.25

    # Trading settings
    trade_size: Decimal = Decimal("0.001")
    max_position_size: Decimal = Decimal("0.01")

    # Zone proximity thresholds
    zone_proximity_pct: float = 0.001  # 0.1% - how close price must be to zone
    min_volume_intensity: float = 0.5  # Minimum zone intensity to trade (0.0-1.0)

    # Risk management
    stop_loss_atr_mult: float = 1.5  # Stop loss as ATR multiple
    take_profit_atr_mult: float = 2.0  # Take profit as ATR multiple


class LiquidationHeatMapStrategy(Strategy):
    """
    Liquidation HeatMap trading strategy.

    Converted from Pine Script: Liquidation HeatMap [BigBeluga]
    Source: https://www.tradingview.com/script/tMtleB1G-Liqudation-HeatMap-BigBeluga/

    Trading Logic:
        - Identifies liquidation zones from pivot highs/lows with volume
        - Enters long when price approaches high-volume zone below
        - Enters short when price approaches high-volume zone above
        - Exits when zone is consumed (price crosses through midpoint)

    The original indicator visualizes liquidation zones. This strategy
    trades reversals at these zones, expecting stop-loss hunting behavior.
    """

    def __init__(self, config: LiquidationHeatMapConfig) -> None:
        super().__init__(config)

        # Configuration
        self.instrument_id = InstrumentId.from_str(config.instrument_id)
        self.bar_type = BarType.from_str(config.bar_type)
        self.trade_size = config.trade_size
        self.max_position_size = config.max_position_size
        self.zone_proximity_pct = config.zone_proximity_pct
        self.min_volume_intensity = config.min_volume_intensity
        self.stop_loss_atr_mult = config.stop_loss_atr_mult
        self.take_profit_atr_mult = config.take_profit_atr_mult

        # Liquidation Zone Indicator
        self.liq_indicator = LiquidationZoneIndicator(
            atr_period=config.atr_period,
            pivot_lookback=config.pivot_lookback,
            max_zones=config.max_zones,
            atr_multiplier=config.atr_multiplier,
        )

        # State
        self.instrument: Optional[Instrument] = None
        self._last_bar: Optional[Bar] = None
        self._current_target_zone: Optional[LiquidationZone] = None

    def on_start(self) -> None:
        """Initialize strategy on start."""
        self.instrument = self.cache.instrument(self.instrument_id)
        if self.instrument is None:
            self.log.error(f"Instrument {self.instrument_id} not found")
            self.stop()
            return

        self.subscribe_bars(self.bar_type)
        self.log.info(f"LiquidationHeatMapStrategy started for {self.instrument_id}")

    def on_bar(self, bar: Bar) -> None:
        """Handle bar updates."""
        self._last_bar = bar

        # Update indicator
        self.liq_indicator.handle_bar(bar)

        if not self.liq_indicator.initialized:
            return

        # Check for trade signals
        self._check_signals(bar)

        # Check for exit conditions
        self._check_exits(bar)

    def _check_signals(self, bar: Bar) -> None:
        """Check for entry signals based on liquidation zones."""
        if not self._is_flat():
            return

        close = float(bar.close)

        # Check zones below price (potential long entries)
        zone_below = self.liq_indicator.nearest_zone_below
        if zone_below and zone_below.volume_intensity >= self.min_volume_intensity:
            distance_pct = (close - zone_below.top) / close
            if distance_pct <= self.zone_proximity_pct:
                self._enter_long(bar, zone_below)
                return

        # Check zones above price (potential short entries)
        zone_above = self.liq_indicator.nearest_zone_above
        if zone_above and zone_above.volume_intensity >= self.min_volume_intensity:
            distance_pct = (zone_above.bottom - close) / close
            if distance_pct <= self.zone_proximity_pct:
                self._enter_short(bar, zone_above)
                return

    def _check_exits(self, bar: Bar) -> None:
        """Check for exit conditions."""
        if self._is_flat():
            return

        # Exit if target zone is consumed
        if self._current_target_zone and self._current_target_zone.consumed:
            self._exit_position(bar, "Zone consumed")

    def _enter_long(self, bar: Bar, zone: LiquidationZone) -> None:
        """Enter long position at liquidation zone."""
        if not self._can_trade():
            return

        self._current_target_zone = zone

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.BUY,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.log.info(
            f"LONG entry @ {bar.close} | Zone: {zone.bottom:.2f}-{zone.top:.2f} | "
            f"Intensity: {zone.volume_intensity:.2f}"
        )

    def _enter_short(self, bar: Bar, zone: LiquidationZone) -> None:
        """Enter short position at liquidation zone."""
        if not self._can_trade():
            return

        self._current_target_zone = zone

        order = self.order_factory.market(
            instrument_id=self.instrument_id,
            order_side=OrderSide.SELL,
            quantity=self.instrument.make_qty(self.trade_size),
            time_in_force=TimeInForce.GTC,
        )
        self.submit_order(order)
        self.log.info(
            f"SHORT entry @ {bar.close} | Zone: {zone.bottom:.2f}-{zone.top:.2f} | "
            f"Intensity: {zone.volume_intensity:.2f}"
        )

    def _exit_position(self, bar: Bar, reason: str) -> None:
        """Exit current position."""
        position = self.portfolio.position(self.instrument_id)
        if position:
            self.close_position(position)
            self.log.info(f"EXIT @ {bar.close} | Reason: {reason}")
            self._current_target_zone = None

    def _is_flat(self) -> bool:
        """Check if no position."""
        return self.portfolio.is_flat(self.instrument_id)

    def _can_trade(self) -> bool:
        """Check if trading is allowed."""
        if self.instrument is None:
            return False

        # Check position limit
        position = self.portfolio.position(self.instrument_id)
        if position:
            current_qty = position.quantity
            if current_qty + self.trade_size > self.max_position_size:
                self.log.warning(
                    f"Position limit: {current_qty} + {self.trade_size} > {self.max_position_size}"
                )
                return False

        return True

    def on_stop(self) -> None:
        """Clean up on stop."""
        self.close_all_positions(self.instrument_id)
        self.cancel_all_orders(self.instrument_id)
        self.log.info("LiquidationHeatMapStrategy stopped")

    # ─────────────────────────────────────────────────────────────────
    # Utility Properties for External Access
    # ─────────────────────────────────────────────────────────────────

    @property
    def active_zones(self) -> list[LiquidationZone]:
        """Get all active liquidation zones."""
        return self.liq_indicator.zones

    @property
    def zones_above(self) -> list[LiquidationZone]:
        """Get zones above current price."""
        return self.liq_indicator.zones_above_price

    @property
    def zones_below(self) -> list[LiquidationZone]:
        """Get zones below current price."""
        return self.liq_indicator.zones_below_price
