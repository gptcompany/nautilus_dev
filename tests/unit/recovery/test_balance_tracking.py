"""Unit tests for balance change tracking during downtime (FR-003 - T033).

Tests:
- Tracking balance changes between cached and exchange state
- Computing balance deltas
- Detecting significant changes
- Logging balance change history
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
    """Factory function to create mock account balances."""
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


@pytest.mark.recovery
class TestBalanceChangeTracking:
    """Tests for tracking balance changes during downtime (T033)."""

    def test_compute_balance_delta_increase(self, mock_cache):
        """Test computing positive delta when balance increased."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(
            currency="USDT", total=Decimal("10000.00")
        )
        exchange_balance = create_mock_account_balance(
            currency="USDT", total=Decimal("12000.00")
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        delta = provider.compute_balance_delta(
            currency="USDT",
            cached=cached_balance,
            exchange=exchange_balance,
        )

        assert delta["currency"] == "USDT"
        assert delta["cached_total"] == Decimal("10000.00")
        assert delta["exchange_total"] == Decimal("12000.00")
        assert delta["total_change"] == Decimal("2000.00")
        assert delta["percent_change"] == pytest.approx(20.0, rel=0.01)

    def test_compute_balance_delta_decrease(self, mock_cache):
        """Test computing negative delta when balance decreased."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(
            currency="USDT", total=Decimal("10000.00")
        )
        exchange_balance = create_mock_account_balance(
            currency="USDT", total=Decimal("8000.00")
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        delta = provider.compute_balance_delta(
            currency="USDT",
            cached=cached_balance,
            exchange=exchange_balance,
        )

        assert delta["total_change"] == Decimal("-2000.00")
        assert delta["percent_change"] == pytest.approx(-20.0, rel=0.01)

    def test_compute_balance_delta_no_change(self, mock_cache):
        """Test computing zero delta when balance unchanged."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(
            currency="USDT", total=Decimal("10000.00")
        )
        exchange_balance = create_mock_account_balance(
            currency="USDT", total=Decimal("10000.00")
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        delta = provider.compute_balance_delta(
            currency="USDT",
            cached=cached_balance,
            exchange=exchange_balance,
        )

        assert delta["total_change"] == Decimal("0.00")
        assert delta["percent_change"] == pytest.approx(0.0, rel=0.01)

    def test_compute_balance_delta_locked_change(self, mock_cache):
        """Test tracking locked balance changes."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(
            currency="USDT",
            total=Decimal("10000.00"),
            locked=Decimal("500.00"),
        )
        exchange_balance = create_mock_account_balance(
            currency="USDT",
            total=Decimal("10000.00"),
            locked=Decimal("2000.00"),
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        delta = provider.compute_balance_delta(
            currency="USDT",
            cached=cached_balance,
            exchange=exchange_balance,
        )

        assert delta["cached_locked"] == Decimal("500.00")
        assert delta["exchange_locked"] == Decimal("2000.00")
        assert delta["locked_change"] == Decimal("1500.00")

    def test_compute_balance_delta_new_currency(self, mock_cache):
        """Test computing delta for new currency (no cached balance)."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        exchange_balance = create_mock_account_balance(
            currency="BTC", total=Decimal("0.5")
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        delta = provider.compute_balance_delta(
            currency="BTC",
            cached=None,
            exchange=exchange_balance,
        )

        assert delta["currency"] == "BTC"
        assert delta["cached_total"] == Decimal("0")
        assert delta["exchange_total"] == Decimal("0.5")
        assert delta["total_change"] == Decimal("0.5")
        assert delta["is_new"] is True

    def test_compute_balance_delta_removed_currency(self, mock_cache):
        """Test computing delta for removed currency (no exchange balance)."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balance = create_mock_account_balance(
            currency="BTC", total=Decimal("0.5")
        )

        provider = PositionRecoveryProvider(cache=mock_cache)
        delta = provider.compute_balance_delta(
            currency="BTC",
            cached=cached_balance,
            exchange=None,
        )

        assert delta["currency"] == "BTC"
        assert delta["cached_total"] == Decimal("0.5")
        assert delta["exchange_total"] == Decimal("0")
        assert delta["total_change"] == Decimal("-0.5")
        assert delta["is_removed"] is True


@pytest.mark.recovery
class TestBalanceChangeHistory:
    """Tests for balance change history tracking."""

    def test_get_balance_changes_returns_all_deltas(self, mock_cache):
        """Test getting all balance changes from reconciliation."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balances = [
            create_mock_account_balance(
                currency="USDT", total=Decimal("10000.00")
            ),
            create_mock_account_balance(
                currency="BTC", total=Decimal("1.0")
            ),
        ]
        exchange_balances = [
            create_mock_account_balance(
                currency="USDT", total=Decimal("12000.00")  # Changed
            ),
            create_mock_account_balance(
                currency="BTC", total=Decimal("0.5")  # Changed
            ),
            create_mock_account_balance(
                currency="ETH", total=Decimal("10.0")  # New
            ),
        ]

        provider = PositionRecoveryProvider(cache=mock_cache)
        deltas = provider.get_balance_changes(
            cached=cached_balances,
            exchange=exchange_balances,
        )

        # Should have 3 deltas: USDT changed, BTC changed, ETH new
        assert len(deltas) == 3
        currencies = {d["currency"] for d in deltas}
        assert currencies == {"USDT", "BTC", "ETH"}

    def test_get_balance_changes_filters_unchanged(self, mock_cache):
        """Test that unchanged balances are not included in changes."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        cached_balances = [
            create_mock_account_balance(
                currency="USDT", total=Decimal("10000.00")
            ),
            create_mock_account_balance(
                currency="BTC", total=Decimal("1.0")
            ),
        ]
        exchange_balances = [
            create_mock_account_balance(
                currency="USDT", total=Decimal("10000.00")  # Same
            ),
            create_mock_account_balance(
                currency="BTC", total=Decimal("0.5")  # Changed
            ),
        ]

        provider = PositionRecoveryProvider(cache=mock_cache)
        deltas = provider.get_balance_changes(
            cached=cached_balances,
            exchange=exchange_balances,
        )

        # Should only have BTC delta
        assert len(deltas) == 1
        assert deltas[0]["currency"] == "BTC"


@pytest.mark.recovery
class TestBalanceChangeSignificance:
    """Tests for detecting significant balance changes."""

    def test_is_significant_change_above_threshold(self, mock_cache):
        """Test detecting significant change above threshold."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache)

        # 15% change should be significant (default threshold 10%)
        delta = {
            "currency": "USDT",
            "total_change": Decimal("1500.00"),
            "percent_change": 15.0,
        }

        assert provider.is_significant_change(delta, threshold_percent=10.0) is True

    def test_is_significant_change_below_threshold(self, mock_cache):
        """Test detecting insignificant change below threshold."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache)

        # 5% change should not be significant (default threshold 10%)
        delta = {
            "currency": "USDT",
            "total_change": Decimal("500.00"),
            "percent_change": 5.0,
        }

        assert provider.is_significant_change(delta, threshold_percent=10.0) is False

    def test_is_significant_change_new_currency_always_significant(self, mock_cache):
        """Test that new currencies are always considered significant."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache)

        delta = {
            "currency": "BTC",
            "total_change": Decimal("0.001"),  # Small amount
            "percent_change": 0.0,  # N/A for new
            "is_new": True,
        }

        assert provider.is_significant_change(delta, threshold_percent=10.0) is True

    def test_is_significant_change_removed_currency_always_significant(
        self, mock_cache
    ):
        """Test that removed currencies are always considered significant."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache)

        delta = {
            "currency": "BTC",
            "total_change": Decimal("-0.001"),  # Small amount
            "percent_change": -100.0,
            "is_removed": True,
        }

        assert provider.is_significant_change(delta, threshold_percent=10.0) is True


@pytest.mark.recovery
class TestBalanceChangeLogging:
    """Tests for logging balance changes."""

    def test_log_balance_changes_logs_warning_for_significant(
        self, mock_cache, mock_logger
    ):
        """Test that significant changes are logged as warnings."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        deltas = [
            {
                "currency": "USDT",
                "total_change": Decimal("1500.00"),
                "percent_change": 15.0,
                "cached_total": Decimal("10000.00"),
                "exchange_total": Decimal("11500.00"),
            },
        ]

        provider.log_balance_changes(deltas, threshold_percent=10.0)

        mock_logger.warning.assert_called()
        # Check that warning contains currency and change info
        call_args = str(mock_logger.warning.call_args)
        assert "USDT" in call_args or "1500" in call_args

    def test_log_balance_changes_logs_info_for_insignificant(
        self, mock_cache, mock_logger
    ):
        """Test that insignificant changes are logged as info."""
        from strategies.common.recovery.provider import PositionRecoveryProvider

        provider = PositionRecoveryProvider(cache=mock_cache, logger=mock_logger)

        deltas = [
            {
                "currency": "USDT",
                "total_change": Decimal("100.00"),
                "percent_change": 1.0,  # Below 10% threshold
                "cached_total": Decimal("10000.00"),
                "exchange_total": Decimal("10100.00"),
            },
        ]

        provider.log_balance_changes(deltas, threshold_percent=10.0)

        # Should use info, not warning
        mock_logger.info.assert_called()
