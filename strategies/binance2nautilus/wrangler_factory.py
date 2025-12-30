"""Wrangler factory for V1/V2 selection.

Provides factory functions that abstract wrangler selection, enabling migration
from V1 (Cython) to V2 (PyO3/Rust) wranglers when BacktestEngine supports PyO3.

Current state (2025-12-24):
- V1 wranglers: Compatible with BacktestEngine (Cython objects)
- V2 wranglers: NOT compatible with BacktestEngine (PyO3 objects rejected)

Migration path:
1. Set config.use_rust_wranglers = True
2. Test with BacktestEngine
3. If works, V2 is now supported
"""

from nautilus_trader.model.data import BarType
from nautilus_trader.model.instruments import Instrument
from nautilus_trader.persistence.wranglers import BarDataWrangler, TradeTickDataWrangler

from .config import ConverterConfig


def get_bar_wrangler(
    bar_type: BarType,
    instrument: Instrument,
    config: ConverterConfig | None = None,
) -> BarDataWrangler:
    """Get a bar data wrangler (V1 or V2 based on config).

    Args:
        bar_type: The bar type specification
        instrument: The instrument for the bars
        config: Converter configuration (optional)

    Returns:
        BarDataWrangler instance

    Note:
        Currently always returns V1 wrangler. When use_rust_wranglers=True
        and BacktestEngine supports PyO3, this will return V2 wrangler.
    """
    config = config or ConverterConfig()

    if config.use_rust_wranglers:
        # V2 wranglers - NOT YET SUPPORTED with BacktestEngine
        # When Rust BacktestEngine is available, uncomment:
        # from nautilus_trader.persistence.wranglers import BarDataWranglerV2
        # return BarDataWranglerV2(bar_type=bar_type, instrument=instrument)
        raise NotImplementedError(
            "V2 wranglers not yet compatible with BacktestEngine. "
            "Set use_rust_wranglers=False in config."
        )

    # V1 wrangler - compatible with BacktestEngine
    return BarDataWrangler(bar_type=bar_type, instrument=instrument)


def get_trade_wrangler(
    instrument: Instrument,
    config: ConverterConfig | None = None,
) -> TradeTickDataWrangler:
    """Get a trade tick data wrangler (V1 or V2 based on config).

    Args:
        instrument: The instrument for the trade ticks
        config: Converter configuration (optional)

    Returns:
        TradeTickDataWrangler instance

    Note:
        Currently always returns V1 wrangler. When use_rust_wranglers=True
        and BacktestEngine supports PyO3, this will return V2 wrangler.
    """
    config = config or ConverterConfig()

    if config.use_rust_wranglers:
        # V2 wranglers - NOT YET SUPPORTED with BacktestEngine
        # When Rust BacktestEngine is available, uncomment:
        # from nautilus_trader.persistence.wranglers import TradeTickDataWranglerV2
        # return TradeTickDataWranglerV2(instrument=instrument)
        raise NotImplementedError(
            "V2 wranglers not yet compatible with BacktestEngine. "
            "Set use_rust_wranglers=False in config."
        )

    # V1 wrangler - compatible with BacktestEngine
    return TradeTickDataWrangler(instrument=instrument)
