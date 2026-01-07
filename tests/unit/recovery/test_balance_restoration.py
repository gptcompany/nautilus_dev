"""Unit tests for balance loading from cache (FR-003 - T032).

Tests:
- Loading balances from Redis cache
- Handling empty cache
- Handling multiple currency balances
- Balance snapshot deserialization
- Getting balances from exchange
- Reconciling cached vs exchange balances
"""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest


def create_mock_account_balance(
    currency: str = "USDT",
    total: Decimal = Decimal("10000.00"),
    locked: Decimal = Decimal("0.00"),
    free: Decimal | None = None,
) -> MagicMock:
    """Factory function to create mock account balances.

    Args:
        currency: Currency code (e.g., USDT, BTC)
        total: Total balance amount
        locked: Locked/reserved amount
        free: Free/available amount (defaults to total - locked)

    Returns:
        MagicMock configured as an AccountBalance object
    """
    if free is None:
        free = total - locked

    balance = MagicMock()
    balance.currency = MagicMock()
    balance.currency.code = currency
    balance.total = MagicMock()
    balance.total.as_decimal.return_value = total
    balance.locked = MagicMock()
    balance.locked.as_decimal.return_value = locked
    balance.free = MagicMock()
    balance.free.as_decimal.return_value = free
    return balance


def create_mock_account(
    account_id: str = "BINANCE-001",
    balances: list | None = None,
) -> MagicMock:
    """Factory function to create mock accounts.

    Args:
        account_id: Account identifier
        balances: List of mock balances

    Returns:
        MagicMock configured as an Account object
    """
    account = MagicMock()
    account.id = MagicMock()
    account.id.value = account_id
    account.balances.return_value = balances or []
    return account


@pytest.mark.recovery
class TestBalanceLoading:
    """Tests for balance loading functionality (T032)."""

    def test_get_cached_balances_empty(self, mock_cache):
        """Test loading balances when cache has no account."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        mock_cache.account.return_value = None

        provider = PositionRecoveryProvider(cache=mock_cache)
        balances = provider.get_cached_balances(trader_id="TESTER-001")

        assert balances == []

    def test_get_cached_balances_single_currency(self, mock_cache):
        """Test loading a single currency balance from cache."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        mock_balance = create_mock_account_balance(
            currency="USDT",
            total=Decimal("10000.00"),
            locked=Decimal("500.00"),
        )
        mock_account = create_mock_account(balances=[mock_balance])
        mock_cache.account.return_value = mock_account

        provider = PositionRecoveryProvider(cache=mock_cache)
        balances = provider.get_cached_balances(trader_id="TESTER-001")

        assert len(balances) == 1
        assert balances[0].currency.code == "USDT"
        assert balances[0].total.as_decimal() == Decimal("10000.00")
        assert balances[0].locked.as_decimal() == Decimal("500.00")
        assert balances[0].free.as_decimal() == Decimal("9500.00")

    def test_get_cached_balances_multiple_currencies(self, mock_cache):
        """Test loading multiple currency balances from cache."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        mock_balances = [
            create_mock_account_balance(currency="USDT", total=Decimal("10000.00")),
            create_mock_account_balance(currency="BTC", total=Decimal("1.5")),
            create_mock_account_balance(currency="ETH", total=Decimal("25.0")),
        ]
        mock_account = create_mock_account(balances=mock_balances)
        mock_cache.account.return_value = mock_account

        provider = PositionRecoveryProvider(cache=mock_cache)
        balances = provider.get_cached_balances(trader_id="TESTER-001")

        assert len(balances) == 3
        currencies = {b.currency.code for b in balances}
        assert currencies == {"USDT", "BTC", "ETH"}

    def test_get_cached_balances_logs_info(self, mock_cache, mock_logger):
        """Test that balance loading logs info messages."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        mock_balance = create_mock_account_balance(currency="USDT")
        mock_account = create_mock_account(balances=[mock_balance])
        mock_cache.account.return_value = mock_account

        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)
        provider.get_cached_balances(trader_id="TESTER-001")

        mock_logger.info.assert_called()


@pytest.mark.recovery
class TestExchangeBalanceLoading:
    """Tests for balance loading from exchange."""

    def test_get_exchange_balances_empty(self, mock_cache):
        """Test getting balances when exchange reports no account."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        mock_cache.account.return_value = None

        provider = PositionRecoveryProvider(cache=mock_cache)
        balances = provider.get_exchange_balances(trader_id="TESTER-001")

        assert balances == []

    def test_get_exchange_balances_returns_account_balances(self, mock_cache):
        """Test that exchange balances are retrieved correctly."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        mock_balance = create_mock_account_balance(
            currency="USDT",
            total=Decimal("15000.00"),
        )
        mock_account = create_mock_account(balances=[mock_balance])
        mock_cache.account.return_value = mock_account

        provider = PositionRecoveryProvider(cache=mock_cache)
        balances = provider.get_exchange_balances(trader_id="TESTER-001")

        assert len(balances) == 1
        assert balances[0].total.as_decimal() == Decimal("15000.00")


@pytest.mark.recovery
class TestBalanceReconciliation:
    """Tests for balance reconciliation between cache and exchange."""

    def test_reconcile_balances_no_changes(self, mock_cache):
        """Test reconciliation when balances match."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))
        exchange_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=[cached_balance],
            exchange=[exchange_balance],
        )

        assert len(reconciled) == 1
        assert len(changes) == 0

    def test_reconcile_balances_total_mismatch(self, mock_cache):
        """Test reconciliation detects total balance mismatch."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))
        exchange_balance = create_mock_account_balance(currency="USDT", total=Decimal("9500.00"))

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=[cached_balance],
            exchange=[exchange_balance],
        )

        assert len(reconciled) == 1
        assert len(changes) == 1
        assert "USDT" in changes[0]
        assert "10000" in changes[0]
        assert "9500" in changes[0]

    def test_reconcile_balances_locked_mismatch(self, mock_cache):
        """Test reconciliation detects locked balance mismatch."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(
            currency="USDT",
            total=Decimal("10000.00"),
            locked=Decimal("500.00"),
        )
        exchange_balance = create_mock_account_balance(
            currency="USDT",
            total=Decimal("10000.00"),
            locked=Decimal("1000.00"),
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=[cached_balance],
            exchange=[exchange_balance],
        )

        assert len(changes) == 1
        assert "locked" in changes[0].lower()

    def test_reconcile_balances_new_currency(self, mock_cache):
        """Test reconciliation detects new currency on exchange."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))
        exchange_balances = [
            create_mock_account_balance(currency="USDT", total=Decimal("10000.00")),
            create_mock_account_balance(currency="BTC", total=Decimal("0.5")),
        ]

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=[cached_balance],
            exchange=exchange_balances,
        )

        assert len(reconciled) == 2
        assert len(changes) == 1
        assert "BTC" in changes[0]
        assert "new" in changes[0].lower() or "external" in changes[0].lower()

    def test_reconcile_balances_removed_currency(self, mock_cache):
        """Test reconciliation detects currency removed from exchange."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balances = [
            create_mock_account_balance(currency="USDT", total=Decimal("10000.00")),
            create_mock_account_balance(currency="BTC", total=Decimal("0.5")),
        ]
        exchange_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=cached_balances,
            exchange=[exchange_balance],
        )

        # Exchange is source of truth - only USDT remains
        assert len(reconciled) == 1
        assert len(changes) == 1
        assert "BTC" in changes[0]

    def test_reconcile_balances_empty_cached(self, mock_cache):
        """Test reconciliation when cached balances are empty."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        exchange_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=[],
            exchange=[exchange_balance],
        )

        assert len(reconciled) == 1
        assert len(changes) == 1  # New balance detected

    def test_reconcile_balances_empty_exchange(self, mock_cache):
        """Test reconciliation when exchange has no balances."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=[cached_balance],
            exchange=[],
        )

        assert len(reconciled) == 0
        assert len(changes) == 1  # Currency removed

    def test_reconcile_balances_exchange_is_source_of_truth(self, mock_cache):
        """Test that exchange balances are returned as reconciled."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(currency="USDT", total=Decimal("10000.00"))
        exchange_balance = create_mock_account_balance(
            currency="USDT",
            total=Decimal("15000.00"),  # Different!
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=[cached_balance],
            exchange=[exchange_balance],
        )

        # Exchange value should be in reconciled
        assert len(reconciled) == 1
        assert reconciled[0].total.as_decimal() == Decimal("15000.00")

    def test_reconcile_balances_multiple_currencies(self, mock_cache):
        """Test reconciliation with multiple currencies."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balances = [
            create_mock_account_balance(currency="USDT", total=Decimal("10000.00")),
            create_mock_account_balance(currency="BTC", total=Decimal("1.0")),
        ]
        exchange_balances = [
            create_mock_account_balance(
                currency="USDT",
                total=Decimal("10000.00"),  # Same
            ),
            create_mock_account_balance(
                currency="BTC",
                total=Decimal("0.5"),  # Changed!
            ),
        ]

        provider = PositionRecoveryProvider(cache=mock_cache)
        reconciled, changes = provider.reconcile_balances(
            cached=cached_balances,
            exchange=exchange_balances,
        )

        assert len(reconciled) == 2
        assert len(changes) == 1  # Only BTC changed
        assert "BTC" in changes[0]
