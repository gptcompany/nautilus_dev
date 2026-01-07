"""Instrument definitions for Binance perpetual futures.

Provides CryptoPerpetual instrument factories for BTCUSDT-PERP and ETHUSDT-PERP.
All instruments use the format: {SYMBOL}-PERP.BINANCE
"""

from datetime import datetime
from decimal import Decimal

import pytz
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.identifiers import InstrumentId, Symbol, Venue
from nautilus_trader.model.instruments import CryptoPerpetual
from nautilus_trader.model.objects import Currency, Money, Price, Quantity

# Standard currencies
BTC = Currency.from_str("BTC")
ETH = Currency.from_str("ETH")
USDT = Currency.from_str("USDT")

# Venue
BINANCE = Venue("BINANCE")


def create_btcusdt_perp(
    ts_event: int | None = None,
    ts_init: int | None = None,
) -> CryptoPerpetual:
    """Create BTCUSDT perpetual futures instrument.

    Args:
        ts_event: Event timestamp in nanoseconds (default: 2019-09-01 UTC)
        ts_init: Init timestamp in nanoseconds (default: same as ts_event)

    Returns:
        CryptoPerpetual instrument for BTCUSDT-PERP.BINANCE
    """
    default_ts = dt_to_unix_nanos(datetime(2019, 9, 1, tzinfo=pytz.UTC))
    ts_event = ts_event or default_ts
    ts_init = ts_init or ts_event

    return CryptoPerpetual(
        instrument_id=InstrumentId(Symbol("BTCUSDT-PERP"), BINANCE),
        raw_symbol=Symbol("BTCUSDT"),
        base_currency=BTC,
        quote_currency=USDT,
        settlement_currency=USDT,
        is_inverse=False,
        price_precision=2,
        size_precision=3,
        price_increment=Price.from_str("0.01"),
        size_increment=Quantity.from_str("0.001"),
        max_quantity=Quantity.from_str("1000"),
        min_quantity=Quantity.from_str("0.001"),
        max_notional=None,
        min_notional=Money(10, USDT),
        max_price=Price.from_str("1000000"),
        min_price=Price.from_str("0.01"),
        margin_init=Decimal("0.05"),
        margin_maint=Decimal("0.025"),
        maker_fee=Decimal("0.0002"),
        taker_fee=Decimal("0.0004"),
        ts_event=ts_event,
        ts_init=ts_init,
    )


def create_ethusdt_perp(
    ts_event: int | None = None,
    ts_init: int | None = None,
) -> CryptoPerpetual:
    """Create ETHUSDT perpetual futures instrument.

    Args:
        ts_event: Event timestamp in nanoseconds (default: 2019-11-01 UTC)
        ts_init: Init timestamp in nanoseconds (default: same as ts_event)

    Returns:
        CryptoPerpetual instrument for ETHUSDT-PERP.BINANCE
    """
    default_ts = dt_to_unix_nanos(datetime(2019, 11, 1, tzinfo=pytz.UTC))
    ts_event = ts_event or default_ts
    ts_init = ts_init or ts_event

    return CryptoPerpetual(
        instrument_id=InstrumentId(Symbol("ETHUSDT-PERP"), BINANCE),
        raw_symbol=Symbol("ETHUSDT"),
        base_currency=ETH,
        quote_currency=USDT,
        settlement_currency=USDT,
        is_inverse=False,
        price_precision=2,
        size_precision=3,
        price_increment=Price.from_str("0.01"),
        size_increment=Quantity.from_str("0.001"),
        max_quantity=Quantity.from_str("10000"),
        min_quantity=Quantity.from_str("0.001"),
        max_notional=None,
        min_notional=Money(10, USDT),
        max_price=Price.from_str("100000"),
        min_price=Price.from_str("0.01"),
        margin_init=Decimal("0.05"),
        margin_maint=Decimal("0.025"),
        maker_fee=Decimal("0.0002"),
        taker_fee=Decimal("0.0004"),
        ts_event=ts_event,
        ts_init=ts_init,
    )


# Instrument registry
_INSTRUMENTS = {
    "BTCUSDT": create_btcusdt_perp,
    "ETHUSDT": create_ethusdt_perp,
}


def get_instrument(
    symbol: str,
    ts_event: int | None = None,
    ts_init: int | None = None,
) -> CryptoPerpetual:
    """Get instrument by symbol.

    Args:
        symbol: Trading symbol (e.g., "BTCUSDT", "ETHUSDT")
        ts_event: Event timestamp in nanoseconds
        ts_init: Init timestamp in nanoseconds

    Returns:
        CryptoPerpetual instrument

    Raises:
        ValueError: If symbol is not supported
    """
    factory = _INSTRUMENTS.get(symbol)
    if factory is None:
        supported = ", ".join(_INSTRUMENTS.keys())
        raise ValueError(f"Unsupported symbol: {symbol}. Supported: {supported}")
    return factory(ts_event=ts_event, ts_init=ts_init)


def list_supported_symbols() -> list[str]:
    """List all supported trading symbols."""
    return list(_INSTRUMENTS.keys())
