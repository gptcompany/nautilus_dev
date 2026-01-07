"""
Order Helper Functions (Spec 015 FR-002).

Utility functions for creating NautilusTrader order objects for Binance execution.
Supports MARKET, LIMIT, STOP_MARKET, and STOP_LIMIT order types.

Notes
-----
- STOP_MARKET and STOP_LIMIT require NautilusTrader Nightly >= 2025-12-10 (Algo Order API)
- All helpers use GTC (Good-Till-Cancel) as default time in force
- reduce_only=True ensures orders only close existing positions

Example Usage
-------------
>>> from nautilus_trader.common.factories import OrderFactory
>>> from nautilus_trader.model.identifiers import InstrumentId, TraderId, StrategyId
>>> from nautilus_trader.model.enums import OrderSide
>>> from nautilus_trader.model.objects import Quantity, Price
>>>
>>> factory = OrderFactory(
...     trader_id=TraderId("TRADER-001"),
...     strategy_id=StrategyId("MyStrategy-001"),
...     clock=LiveClock(),
... )
>>> instrument_id = InstrumentId.from_str("BTCUSDT-PERP.BINANCE")
>>>
>>> # Market order
>>> order = create_market_order(factory, instrument_id, OrderSide.BUY, Quantity.from_str("0.1"))
>>>
>>> # Limit order with post_only
>>> order = create_limit_order(
...     factory, instrument_id, OrderSide.SELL,
...     Quantity.from_str("0.1"), Price.from_str("50000"),
...     post_only=True
... )
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nautilus_trader.model.enums import OrderSide, TimeInForce, TriggerType
from nautilus_trader.model.identifiers import InstrumentId

if TYPE_CHECKING:
    from nautilus_trader.common.factories import OrderFactory
    from nautilus_trader.model.objects import Price, Quantity
    from nautilus_trader.model.orders import (
        LimitOrder,
        MarketOrder,
        StopLimitOrder,
        StopMarketOrder,
    )


def validate_order_params(
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: "Quantity",
    price: "Price | None" = None,
    trigger_price: "Price | None" = None,
) -> None:
    """
    Validate order parameters before submission.

    Parameters
    ----------
    instrument_id : InstrumentId
        The instrument to trade.
    side : OrderSide
        Order side (BUY or SELL).
    quantity : Quantity
        Order quantity.
    price : Price, optional
        Limit price (required for LIMIT orders).
    trigger_price : Price, optional
        Trigger price (required for STOP orders).

    Raises
    ------
    ValueError
        If any parameter is invalid.
    """
    if not isinstance(instrument_id, InstrumentId):
        raise ValueError(f"instrument_id must be InstrumentId, got {type(instrument_id)}")

    if not isinstance(side, OrderSide):
        raise ValueError(f"side must be OrderSide, got {type(side)}")

    if quantity is None:
        raise ValueError("quantity must not be None")

    if quantity.as_double() <= 0:
        raise ValueError(f"quantity must be positive, got {quantity}")

    if price is not None and price.as_double() <= 0:
        raise ValueError(f"price must be positive, got {price}")

    if trigger_price is not None and trigger_price.as_double() <= 0:
        raise ValueError(f"trigger_price must be positive, got {trigger_price}")


def create_market_order(
    order_factory: "OrderFactory",
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: "Quantity",
    reduce_only: bool = False,
    tags: list[str] | None = None,
) -> "MarketOrder":
    """
    Create a market order for immediate execution.

    Parameters
    ----------
    order_factory : OrderFactory
        The order factory instance.
    instrument_id : InstrumentId
        The instrument to trade (e.g., "BTCUSDT-PERP.BINANCE").
    side : OrderSide
        Order side (BUY or SELL).
    quantity : Quantity
        Order quantity.
    reduce_only : bool, default False
        If True, order can only reduce an existing position.
    tags : list[str], optional
        Custom tags for order identification.

    Returns
    -------
    MarketOrder
        The market order object ready for submission.

    Example
    -------
    >>> order = create_market_order(factory, instrument_id, OrderSide.BUY, Quantity.from_str("0.1"))
    """
    validate_order_params(instrument_id, side, quantity)

    return order_factory.market(
        instrument_id=instrument_id,
        order_side=side,
        quantity=quantity,
        time_in_force=TimeInForce.GTC,
        reduce_only=reduce_only,
        tags=tags,
    )


def create_limit_order(
    order_factory: "OrderFactory",
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: "Quantity",
    price: "Price",
    post_only: bool = False,
    reduce_only: bool = False,
    time_in_force: TimeInForce = TimeInForce.GTC,
    tags: list[str] | None = None,
) -> "LimitOrder":
    """
    Create a limit order at a specified price.

    Parameters
    ----------
    order_factory : OrderFactory
        The order factory instance.
    instrument_id : InstrumentId
        The instrument to trade.
    side : OrderSide
        Order side (BUY or SELL).
    quantity : Quantity
        Order quantity.
    price : Price
        Limit price.
    post_only : bool, default False
        If True, order will only be maker (added to book, not matched immediately).
        If it would match immediately, it will be rejected.
    reduce_only : bool, default False
        If True, order can only reduce an existing position.
    time_in_force : TimeInForce, default GTC
        Time in force for the order.
    tags : list[str], optional
        Custom tags for order identification.

    Returns
    -------
    LimitOrder
        The limit order object ready for submission.

    Example
    -------
    >>> order = create_limit_order(
    ...     factory, instrument_id, OrderSide.SELL,
    ...     Quantity.from_str("0.1"), Price.from_str("50000"),
    ...     post_only=True  # Maker only
    ... )
    """
    validate_order_params(instrument_id, side, quantity, price=price)

    return order_factory.limit(
        instrument_id=instrument_id,
        order_side=side,
        quantity=quantity,
        price=price,
        time_in_force=time_in_force,
        post_only=post_only,
        reduce_only=reduce_only,
        tags=tags,
    )


def create_stop_market_order(
    order_factory: "OrderFactory",
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: "Quantity",
    trigger_price: "Price",
    trigger_type: TriggerType = TriggerType.LAST_PRICE,
    reduce_only: bool = False,
    tags: list[str] | None = None,
) -> "StopMarketOrder":
    """
    Create a stop-market order (Algo Order API).

    The order becomes a market order when trigger_price is reached.
    Requires NautilusTrader Nightly >= 2025-12-10 for Binance support.

    Parameters
    ----------
    order_factory : OrderFactory
        The order factory instance.
    instrument_id : InstrumentId
        The instrument to trade.
    side : OrderSide
        Order side (BUY or SELL).
    quantity : Quantity
        Order quantity.
    trigger_price : Price
        Price at which the order triggers.
    trigger_type : TriggerType, default LAST_PRICE
        Trigger type (LAST_PRICE, MARK_PRICE, INDEX_PRICE).
    reduce_only : bool, default False
        If True, order can only reduce an existing position.
    tags : list[str], optional
        Custom tags for order identification.

    Returns
    -------
    StopMarketOrder
        The stop-market order object ready for submission.

    Notes
    -----
    For stop-loss orders:
    - LONG position: side=SELL, trigger_price < current_price
    - SHORT position: side=BUY, trigger_price > current_price

    Example
    -------
    >>> # Stop-loss for long position
    >>> order = create_stop_market_order(
    ...     factory, instrument_id, OrderSide.SELL,
    ...     Quantity.from_str("0.1"), Price.from_str("40000"),
    ...     reduce_only=True
    ... )
    """
    validate_order_params(instrument_id, side, quantity, trigger_price=trigger_price)

    return order_factory.stop_market(
        instrument_id=instrument_id,
        order_side=side,
        quantity=quantity,
        trigger_price=trigger_price,
        trigger_type=trigger_type,
        time_in_force=TimeInForce.GTC,
        reduce_only=reduce_only,
        tags=tags,
    )


def create_stop_limit_order(
    order_factory: "OrderFactory",
    instrument_id: InstrumentId,
    side: OrderSide,
    quantity: "Quantity",
    price: "Price",
    trigger_price: "Price",
    trigger_type: TriggerType = TriggerType.LAST_PRICE,
    post_only: bool = False,
    reduce_only: bool = False,
    tags: list[str] | None = None,
) -> "StopLimitOrder":
    """
    Create a stop-limit order (Algo Order API).

    The order becomes a limit order at `price` when `trigger_price` is reached.
    Requires NautilusTrader Nightly >= 2025-12-10 for Binance support.

    Parameters
    ----------
    order_factory : OrderFactory
        The order factory instance.
    instrument_id : InstrumentId
        The instrument to trade.
    side : OrderSide
        Order side (BUY or SELL).
    quantity : Quantity
        Order quantity.
    price : Price
        Limit price for the order after trigger.
    trigger_price : Price
        Price at which the order triggers.
    trigger_type : TriggerType, default LAST_PRICE
        Trigger type (LAST_PRICE, MARK_PRICE, INDEX_PRICE).
    post_only : bool, default False
        If True, limit order will only be maker.
    reduce_only : bool, default False
        If True, order can only reduce an existing position.
    tags : list[str], optional
        Custom tags for order identification.

    Returns
    -------
    StopLimitOrder
        The stop-limit order object ready for submission.

    Example
    -------
    >>> # Stop-limit order with slippage protection
    >>> order = create_stop_limit_order(
    ...     factory, instrument_id, OrderSide.SELL,
    ...     Quantity.from_str("0.1"),
    ...     Price.from_str("39500"),   # Limit price
    ...     Price.from_str("40000"),   # Trigger price
    ... )
    """
    validate_order_params(instrument_id, side, quantity, price=price, trigger_price=trigger_price)

    return order_factory.stop_limit(
        instrument_id=instrument_id,
        order_side=side,
        quantity=quantity,
        price=price,
        trigger_price=trigger_price,
        trigger_type=trigger_type,
        time_in_force=TimeInForce.GTC,
        post_only=post_only,
        reduce_only=reduce_only,
        tags=tags,
    )


def create_external_claims(
    instrument_ids: list[str],
) -> list[InstrumentId]:
    """
    Create external order claims for position reconciliation.

    Use this when restarting a TradingNode that may have existing positions
    on the exchange that need to be claimed by a strategy.

    Parameters
    ----------
    instrument_ids : list[str]
        List of instrument ID strings (e.g., ["BTCUSDT-PERP.BINANCE"]).

    Returns
    -------
    list[InstrumentId]
        List of InstrumentId objects for external_order_claims config.

    Example
    -------
    >>> from nautilus_trader.config import StrategyConfig
    >>>
    >>> claims = create_external_claims([
    ...     "BTCUSDT-PERP.BINANCE",
    ...     "ETHUSDT-PERP.BINANCE",
    ... ])
    >>>
    >>> config = MyStrategyConfig(
    ...     instrument_id="BTCUSDT-PERP.BINANCE",
    ...     external_order_claims=claims,
    ... )

    Notes
    -----
    External order claims are essential for:
    1. Recovery after TradingNode restart
    2. Reconciliation of positions opened outside NautilusTrader
    3. Multi-strategy deployments sharing instruments

    Without claims, existing positions may not be properly managed by strategies.
    """
    return [InstrumentId.from_str(id_str) for id_str in instrument_ids]
