"""Position Recovery Provider (Spec 017).

This module implements the PositionRecoveryProvider for loading positions
from cache and reconciling them with exchange state.

Key Responsibilities:
- Load cached positions from NautilusTrader cache
- Query current exchange positions
- Reconcile discrepancies (exchange is source of truth)
- Generate discrepancy messages for logging
- Load cached balances (FR-003)
- Query exchange balances (FR-003)
- Reconcile and track balance changes (FR-003)

Implementation Note:
    Selected via Alpha-Evolve process from 3 approaches:
    - Approach A: Simple Iterative (O(n*m)) - rejected for performance
    - Approach B: Dictionary-Based (O(n+m)) - SELECTED (winner)
    - Approach C: Dataclass-Based - rejected for over-engineering
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nautilus_trader.model.identifiers import TraderId
    from nautilus_trader.model.position import Position


# Module logger
_log = logging.getLogger(__name__)


class PositionRecoveryProvider:
    """Provider for position recovery and reconciliation.

    Implements the PositionRecoveryProvider interface from Spec 017.
    Uses dictionary-based lookups for O(n+m) reconciliation complexity.

    Attributes:
        cache: NautilusTrader cache instance for position access.
        logger: Optional custom logger instance.
        discrepancy_count: Number of discrepancies found in last reconciliation.

    Example:
        >>> provider = PositionRecoveryProvider(cache=node.cache)
        >>> cached = provider.get_cached_positions(trader_id="TRADER-001")
        >>> exchange = provider.get_exchange_positions(trader_id="TRADER-001")
        >>> reconciled, discrepancies = provider.reconcile_positions(cached, exchange)
    """

    def __init__(
        self,
        cache: Any,
        logger: logging.Logger | None = None,
    ) -> None:
        """Initialize the PositionRecoveryProvider.

        Args:
            cache: NautilusTrader cache instance.
            logger: Optional custom logger. If None, uses module logger.
        """
        self._cache = cache
        self._log = logger or _log
        self._discrepancy_count: int = 0
        self._balance_change_count: int = 0

    @property
    def discrepancy_count(self) -> int:
        """Number of discrepancies found in the last reconciliation.

        Returns:
            Count of discrepancies from the most recent reconcile_positions() call.
        """
        return self._discrepancy_count

    @property
    def balance_change_count(self) -> int:
        """Number of balance changes found in the last reconciliation.

        Returns:
            Count of balance changes from the most recent reconcile_balances() call.
        """
        return self._balance_change_count

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
        self._log.info("Loading cached positions for trader_id=%s", trader_id)

        positions = list(self._cache.positions())

        self._log.info(
            "Loaded %d positions from cache for trader_id=%s",
            len(positions),
            trader_id,
        )

        # Log individual positions at DEBUG level
        for pos in positions:
            self._log.debug(
                "Cached position: instrument=%s side=%s qty=%s",
                pos.instrument_id.value,
                pos.side.value,
                pos.quantity.as_decimal(),
            )

        return positions

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
        self._log.info("Querying exchange positions for trader_id=%s", trader_id)

        # Default implementation returns cache positions
        # In production, override to query exchange directly
        positions = list(self._cache.positions())

        self._log.info(
            "Retrieved %d positions from exchange for trader_id=%s",
            len(positions),
            trader_id,
        )

        # Log individual positions at DEBUG level
        for pos in positions:
            self._log.debug(
                "Exchange position: instrument=%s side=%s qty=%s",
                pos.instrument_id.value,
                pos.side.value,
                pos.quantity.as_decimal(),
            )

        return positions

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
        self._log.info(
            "Reconciling positions: cached=%d exchange=%d",
            len(cached),
            len(exchange),
        )

        reconciled: list[Position] = []
        discrepancies: list[str] = []

        # Warn about duplicate instrument_ids (B5 fix)
        cached_ids = [pos.instrument_id.value for pos in cached]
        if len(cached_ids) != len(set(cached_ids)):
            seen: set[str] = set()
            for iid in cached_ids:
                if iid in seen:
                    self._log.warning("Duplicate instrument_id in cached positions: %s", iid)
                seen.add(iid)

        exchange_ids = [pos.instrument_id.value for pos in exchange]
        if len(exchange_ids) != len(set(exchange_ids)):
            seen = set()
            for iid in exchange_ids:
                if iid in seen:
                    self._log.warning("Duplicate instrument_id in exchange positions: %s", iid)
                seen.add(iid)

        # Build lookup maps for O(1) access - O(n) + O(m)
        cached_map: dict[str, Position] = {pos.instrument_id.value: pos for pos in cached}
        exchange_map: dict[str, Position] = {pos.instrument_id.value: pos for pos in exchange}

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
                    msg = (
                        f"Quantity mismatch for {instrument_id}: "
                        f"cached={cached_qty}, exchange={ex_qty}"
                    )
                    discrepancies.append(msg)
                    self._log.warning(msg)

                # Check for side mismatch
                if cached_side != ex_side:
                    msg = (
                        f"Side mismatch for {instrument_id}: "
                        f"cached={cached_side}, exchange={ex_side}"
                    )
                    discrepancies.append(msg)
                    self._log.warning(msg)

                if cached_qty == ex_qty and cached_side == ex_side:
                    self._log.debug(
                        "Position matches: %s %s %s",
                        instrument_id,
                        ex_side,
                        ex_qty,
                    )
            else:
                # External position (on exchange but not in cache)
                msg = f"External position detected: {instrument_id} {ex_side} {ex_qty}"
                discrepancies.append(msg)
                self._log.warning(msg)

            # Exchange is source of truth - add to reconciled
            reconciled.append(ex_pos)

        # Find positions closed on exchange (in cache but not on exchange) - O(n)
        for instrument_id in cached_map:
            if instrument_id not in exchange_map:
                msg = f"Position closed on exchange: {instrument_id} (missing from exchange)"
                discrepancies.append(msg)
                self._log.warning(msg)

        # Update discrepancy count
        self._discrepancy_count = len(discrepancies)

        self._log.info(
            "Reconciliation complete: reconciled=%d discrepancies=%d",
            len(reconciled),
            len(discrepancies),
        )

        return reconciled, discrepancies

    # ========================================================================
    # FR-003: Balance Restoration Methods
    # ========================================================================

    def get_cached_balances(self, trader_id: str | TraderId) -> list[Any]:
        """Load balances from cache.

        Retrieves all account balances from the NautilusTrader cache.

        Args:
            trader_id: The trader identifier (used for logging context).

        Returns:
            List of cached account balances. Empty list if no account.
        """
        self._log.info("Loading cached balances for trader_id=%s", trader_id)

        account = self._cache.account()
        if account is None:
            self._log.info("No account in cache for trader_id=%s", trader_id)
            return []

        balances = list(account.balances())

        self._log.info(
            "Loaded %d balances from cache for trader_id=%s",
            len(balances),
            trader_id,
        )

        # Log individual balances at DEBUG level
        for bal in balances:
            self._log.debug(
                "Cached balance: currency=%s total=%s locked=%s free=%s",
                bal.currency.code,
                bal.total.as_decimal(),
                bal.locked.as_decimal(),
                bal.free.as_decimal(),
            )

        return balances

    def get_exchange_balances(self, trader_id: str | TraderId) -> list[Any]:
        """Query current balances from exchange.

        In live trading, this would query the exchange directly.
        For testing/simulation, returns balances from cache.

        Note:
            In production, this method should be overridden to query
            the actual exchange via the execution client.

        Args:
            trader_id: The trader identifier.

        Returns:
            List of balances reported by exchange. Empty list if no account.
        """
        self._log.info("Querying exchange balances for trader_id=%s", trader_id)

        # Default implementation returns cache account balances
        # In production, override to query exchange directly
        account = self._cache.account()
        if account is None:
            self._log.info("No account from exchange for trader_id=%s", trader_id)
            return []

        balances = list(account.balances())

        self._log.info(
            "Retrieved %d balances from exchange for trader_id=%s",
            len(balances),
            trader_id,
        )

        # Log individual balances at DEBUG level
        for bal in balances:
            self._log.debug(
                "Exchange balance: currency=%s total=%s locked=%s free=%s",
                bal.currency.code,
                bal.total.as_decimal(),
                bal.locked.as_decimal(),
                bal.free.as_decimal(),
            )

        return balances

    def reconcile_balances(
        self,
        cached: list[Any],
        exchange: list[Any],
    ) -> tuple[list[Any], list[str]]:
        """Reconcile cached balances with exchange balances.

        Compares balances by currency and detects changes:
        - Total balance mismatches
        - Locked balance mismatches
        - New currencies (on exchange but not in cache)
        - Removed currencies (in cache but not on exchange)

        The exchange is always the SOURCE OF TRUTH. Reconciled balances
        are the exchange balances, not the cached ones.

        Args:
            cached: Balances loaded from cache.
            exchange: Balances from exchange query.

        Returns:
            Tuple of (reconciled_balances, change_messages).
            - reconciled_balances: List of exchange balances (source of truth)
            - change_messages: List of human-readable change strings
        """
        self._log.info(
            "Reconciling balances: cached=%d exchange=%d",
            len(cached),
            len(exchange),
        )

        reconciled: list[Any] = []
        changes: list[str] = []

        # Build lookup maps for O(1) access
        cached_map: dict[str, Any] = {bal.currency.code: bal for bal in cached}
        exchange_map: dict[str, Any] = {bal.currency.code: bal for bal in exchange}

        # Process exchange balances (source of truth)
        for currency, ex_bal in exchange_map.items():
            ex_total = ex_bal.total.as_decimal()
            ex_locked = ex_bal.locked.as_decimal()

            if currency in cached_map:
                # Balance exists in both cache and exchange
                cached_bal = cached_map[currency]
                cached_total = cached_bal.total.as_decimal()
                cached_locked = cached_bal.locked.as_decimal()

                # Check for total mismatch
                if cached_total != ex_total:
                    msg = (
                        f"Total balance mismatch for {currency}: "
                        f"cached={cached_total}, exchange={ex_total}"
                    )
                    changes.append(msg)
                    self._log.warning(msg)

                # Check for locked mismatch
                elif cached_locked != ex_locked:
                    msg = (
                        f"Locked balance mismatch for {currency}: "
                        f"cached={cached_locked}, exchange={ex_locked}"
                    )
                    changes.append(msg)
                    self._log.warning(msg)

                else:
                    self._log.debug(
                        "Balance matches: %s total=%s locked=%s",
                        currency,
                        ex_total,
                        ex_locked,
                    )
            else:
                # New currency (on exchange but not in cache)
                msg = f"New balance detected: {currency} total={ex_total}"
                changes.append(msg)
                self._log.warning(msg)

            # Exchange is source of truth - add to reconciled
            reconciled.append(ex_bal)

        # Find balances removed from exchange (in cache but not on exchange)
        for currency in cached_map:
            if currency not in exchange_map:
                cached_total = cached_map[currency].total.as_decimal()
                msg = f"Balance removed from exchange: {currency} (was {cached_total})"
                changes.append(msg)
                self._log.warning(msg)

        # Update change count
        self._balance_change_count = len(changes)

        self._log.info(
            "Balance reconciliation complete: reconciled=%d changes=%d",
            len(reconciled),
            len(changes),
        )

        return reconciled, changes

    def compute_balance_delta(
        self,
        currency: str,
        cached: Any | None,
        exchange: Any | None,
    ) -> dict[str, Any]:
        """Compute detailed delta between cached and exchange balance.

        Args:
            currency: Currency code (e.g., "USDT", "BTC").
            cached: Cached balance object (or None if new).
            exchange: Exchange balance object (or None if removed).

        Returns:
            Dictionary with delta details:
            - currency: Currency code
            - cached_total: Cached total balance (0 if new)
            - exchange_total: Exchange total balance (0 if removed)
            - total_change: Absolute change in total
            - percent_change: Percent change (0 if cached was 0)
            - cached_locked: Cached locked balance
            - exchange_locked: Exchange locked balance
            - locked_change: Change in locked balance
            - is_new: True if currency is new (not in cache)
            - is_removed: True if currency was removed (not on exchange)
        """
        # Extract values or defaults
        cached_total = cached.total.as_decimal() if cached is not None else Decimal("0")
        cached_locked = cached.locked.as_decimal() if cached is not None else Decimal("0")
        exchange_total = exchange.total.as_decimal() if exchange is not None else Decimal("0")
        exchange_locked = exchange.locked.as_decimal() if exchange is not None else Decimal("0")

        total_change = exchange_total - cached_total
        locked_change = exchange_locked - cached_locked

        # Calculate percent change (avoid division by zero)
        if cached_total != Decimal("0"):
            percent_change = float((total_change / cached_total) * Decimal("100"))
        else:
            percent_change = 0.0 if exchange_total == Decimal("0") else 100.0

        return {
            "currency": currency,
            "cached_total": cached_total,
            "exchange_total": exchange_total,
            "total_change": total_change,
            "percent_change": percent_change,
            "cached_locked": cached_locked,
            "exchange_locked": exchange_locked,
            "locked_change": locked_change,
            "is_new": cached is None,
            "is_removed": exchange is None,
        }

    def get_balance_changes(
        self,
        cached: list[Any],
        exchange: list[Any],
    ) -> list[dict[str, Any]]:
        """Get all balance changes between cached and exchange state.

        Only returns deltas for currencies that have changed.

        Args:
            cached: Balances loaded from cache.
            exchange: Balances from exchange query.

        Returns:
            List of delta dictionaries for changed currencies.
        """
        # Build lookup maps
        cached_map: dict[str, Any] = {bal.currency.code: bal for bal in cached}
        exchange_map: dict[str, Any] = {bal.currency.code: bal for bal in exchange}

        all_currencies = set(cached_map.keys()) | set(exchange_map.keys())
        deltas: list[dict[str, Any]] = []

        for currency in all_currencies:
            cached_bal = cached_map.get(currency)
            exchange_bal = exchange_map.get(currency)

            delta = self.compute_balance_delta(
                currency=currency,
                cached=cached_bal,
                exchange=exchange_bal,
            )

            # Only include if there's a change
            if (
                delta["total_change"] != Decimal("0")
                or delta["locked_change"] != Decimal("0")
                or delta["is_new"]
                or delta["is_removed"]
            ):
                deltas.append(delta)

        return deltas

    def is_significant_change(
        self,
        delta: dict[str, Any],
        threshold_percent: float = 10.0,
    ) -> bool:
        """Check if a balance change is significant.

        New and removed currencies are always considered significant.
        Otherwise, significance is determined by percent change threshold.

        Args:
            delta: Delta dictionary from compute_balance_delta().
            threshold_percent: Minimum percent change to be significant.

        Returns:
            True if change is significant, False otherwise.
        """
        # New and removed currencies are always significant
        if delta.get("is_new", False) or delta.get("is_removed", False):
            return True

        # Check if percent change exceeds threshold
        return bool(abs(delta.get("percent_change", 0.0)) >= threshold_percent)

    def log_balance_changes(
        self,
        deltas: list[dict[str, Any]],
        threshold_percent: float = 10.0,
    ) -> None:
        """Log balance changes with appropriate severity.

        Significant changes are logged as warnings, others as info.

        Args:
            deltas: List of delta dictionaries.
            threshold_percent: Threshold for significant changes.
        """
        for delta in deltas:
            currency = delta["currency"]
            cached_total = delta.get("cached_total", Decimal("0"))
            exchange_total = delta.get("exchange_total", Decimal("0"))
            total_change = delta.get("total_change", Decimal("0"))
            percent_change = delta.get("percent_change", 0.0)

            msg = (
                f"Balance change for {currency}: "
                f"{cached_total} -> {exchange_total} "
                f"(change: {total_change}, {percent_change:.2f}%)"
            )

            if self.is_significant_change(delta, threshold_percent):
                self._log.warning(msg)
            else:
                self._log.info(msg)
