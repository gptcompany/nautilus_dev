"""Position Recovery Provider (Spec 017).

This module implements the PositionRecoveryProvider for loading positions
from cache and reconciling them with exchange state.

Key Responsibilities:
- Load cached positions from NautilusTrader cache
- Query current exchange positions
- Reconcile discrepancies (exchange is source of truth)
- Generate discrepancy messages for logging

Implementation Note:
    Selected via Alpha-Evolve process from 3 approaches:
    - Approach A: Simple Iterative (O(n*m)) - rejected for performance
    - Approach B: Dictionary-Based (O(n+m)) - SELECTED (winner)
    - Approach C: Dataclass-Based - rejected for over-engineering
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nautilus_trader.model.identifiers import TraderId
    from nautilus_trader.model.position import Position


class PositionRecoveryProvider:
    """Provider for position recovery and reconciliation.

    Implements the PositionRecoveryProvider interface from Spec 017.
    Uses dictionary-based lookups for O(n+m) reconciliation complexity.

    Attributes:
        cache: NautilusTrader cache instance for position access.

    Example:
        >>> provider = PositionRecoveryProvider(cache=node.cache)
        >>> cached = provider.get_cached_positions(trader_id="TRADER-001")
        >>> exchange = provider.get_exchange_positions(trader_id="TRADER-001")
        >>> reconciled, discrepancies = provider.reconcile_positions(cached, exchange)
    """

    def __init__(self, cache: Any) -> None:
        """Initialize the PositionRecoveryProvider.

        Args:
            cache: NautilusTrader cache instance.
        """
        self._cache = cache

    def get_cached_positions(self, trader_id: str | TraderId) -> list[Position]:
        """Load positions from cache.

        Retrieves all positions from the NautilusTrader cache.
        Both open and closed positions are returned; filtering is
        the caller's responsibility.

        Args:
            trader_id: The trader identifier (used for logging context).

        Returns:
            List of cached positions.
        """
        return list(self._cache.positions())

    def get_exchange_positions(self, trader_id: str | TraderId) -> list[Position]:
        """Query current positions from exchange.

        In live trading, this would query the exchange directly.
        For testing/simulation, returns positions from cache.

        Note:
            In production, this method should be overridden to query
            the actual exchange via the execution client.

        Args:
            trader_id: The trader identifier.

        Returns:
            List of positions reported by exchange.
        """
        # Default implementation returns cache positions
        # In production, override to query exchange directly
        return list(self._cache.positions())

    def reconcile_positions(
        self,
        cached: list[Position],
        exchange: list[Position],
    ) -> tuple[list[Position], list[str]]:
        """Reconcile cached positions with exchange positions.

        Compares positions by instrument_id and detects discrepancies:
        - Quantity mismatches (cache vs exchange quantity differs)
        - Side mismatches (cache LONG but exchange SHORT, or vice versa)
        - External positions (on exchange but not in cache)
        - Closed positions (in cache but not on exchange)

        The exchange is always the SOURCE OF TRUTH. Reconciled positions
        are the exchange positions, not the cached ones.

        Args:
            cached: Positions loaded from cache.
            exchange: Positions from exchange query.

        Returns:
            Tuple of (reconciled_positions, discrepancy_messages).
            - reconciled_positions: List of exchange positions (source of truth)
            - discrepancy_messages: List of human-readable discrepancy strings

        Example:
            >>> reconciled, discrepancies = provider.reconcile_positions(
            ...     cached=[cached_btc],
            ...     exchange=[exchange_btc, exchange_eth],
            ... )
            >>> for msg in discrepancies:
            ...     logger.warning(msg)
        """
        reconciled: list[Position] = []
        discrepancies: list[str] = []

        # Build lookup maps for O(1) access - O(n) + O(m)
        cached_map: dict[str, Position] = {
            pos.instrument_id.value: pos for pos in cached
        }
        exchange_map: dict[str, Position] = {
            pos.instrument_id.value: pos for pos in exchange
        }

        # Process exchange positions (source of truth) - O(m)
        for instrument_id, ex_pos in exchange_map.items():
            ex_qty = ex_pos.quantity.as_decimal()
            ex_side = ex_pos.side.value

            if instrument_id in cached_map:
                # Position exists in both cache and exchange
                cached_pos = cached_map[instrument_id]
                cached_qty = cached_pos.quantity.as_decimal()
                cached_side = cached_pos.side.value

                # Check for quantity mismatch
                if cached_qty != ex_qty:
                    discrepancies.append(
                        f"Quantity mismatch for {instrument_id}: "
                        f"cached={cached_qty}, exchange={ex_qty}"
                    )

                # Check for side mismatch
                if cached_side != ex_side:
                    discrepancies.append(
                        f"Side mismatch for {instrument_id}: "
                        f"cached={cached_side}, exchange={ex_side}"
                    )
            else:
                # External position (on exchange but not in cache)
                discrepancies.append(
                    f"External position detected: {instrument_id} {ex_side} {ex_qty}"
                )

            # Exchange is source of truth - add to reconciled
            reconciled.append(ex_pos)

        # Find positions closed on exchange (in cache but not on exchange) - O(n)
        for instrument_id in cached_map:
            if instrument_id not in exchange_map:
                discrepancies.append(
                    f"Position closed on exchange: {instrument_id} "
                    f"(missing from exchange)"
                )

        return reconciled, discrepancies
