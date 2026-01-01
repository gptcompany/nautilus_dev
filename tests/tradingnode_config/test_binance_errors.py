"""
Unit tests for Binance Error Handling (Spec 015 FR-004).

Tests error classification, retry logic, and backoff calculations.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add project root to sys.path for imports
_project_root = Path(__file__).parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))


from config.binance_errors import (  # noqa: E402
    ALGO_ORDER_REQUIRED,
    DISCONNECTED,
    INVALID_SIGNATURE,
    NEW_ORDER_REJECTED,
    TOO_MANY_REQUESTS,
    UNAUTHORIZED,
    BinanceErrorCategory,
    calculate_backoff_delay,
    get_error_category,
    get_error_message,
    is_retryable_error,
    should_retry,
)


class TestIsRetryableError:
    """Tests for is_retryable_error function."""

    def test_rate_limit_is_retryable(self):
        """Rate limit errors should be retryable."""
        assert is_retryable_error(TOO_MANY_REQUESTS) is True

    def test_disconnected_is_retryable(self):
        """Network disconnect should be retryable."""
        assert is_retryable_error(DISCONNECTED) is True

    def test_unauthorized_not_retryable(self):
        """Authentication errors should not be retryable."""
        assert is_retryable_error(UNAUTHORIZED) is False

    def test_invalid_signature_not_retryable(self):
        """Signature errors should not be retryable."""
        assert is_retryable_error(INVALID_SIGNATURE) is False

    def test_order_rejected_not_retryable(self):
        """Order rejection should not be retryable."""
        assert is_retryable_error(NEW_ORDER_REJECTED) is False

    def test_algo_order_required_not_retryable(self):
        """Algo order requirement error should not be retryable."""
        assert is_retryable_error(ALGO_ORDER_REQUIRED) is False

    def test_unknown_error_is_retryable(self):
        """Unknown error codes should be retryable by default."""
        assert is_retryable_error(-9999) is True


class TestGetErrorMessage:
    """Tests for get_error_message function."""

    def test_known_error_code(self):
        """Should return message for known error codes."""
        msg = get_error_message(TOO_MANY_REQUESTS)
        assert "-1003" in msg
        assert "Rate limited" in msg

    def test_unknown_error_code(self):
        """Should handle unknown error codes."""
        msg = get_error_message(-9999)
        assert "-9999" in msg
        assert "Unknown" in msg


class TestGetErrorCategory:
    """Tests for get_error_category function."""

    def test_rate_limit_category(self):
        """Rate limit should be RATE_LIMIT category."""
        assert get_error_category(TOO_MANY_REQUESTS) == BinanceErrorCategory.RATE_LIMIT

    def test_network_category(self):
        """Disconnected should be NETWORK category."""
        assert get_error_category(DISCONNECTED) == BinanceErrorCategory.NETWORK

    def test_auth_category(self):
        """Unauthorized should be AUTHENTICATION category."""
        assert get_error_category(UNAUTHORIZED) == BinanceErrorCategory.AUTHENTICATION

    def test_order_category(self):
        """Order rejected should be ORDER category."""
        assert get_error_category(NEW_ORDER_REJECTED) == BinanceErrorCategory.ORDER

    def test_unknown_category(self):
        """Unknown error should be UNKNOWN category."""
        assert get_error_category(-9999) == BinanceErrorCategory.UNKNOWN


class TestCalculateBackoffDelay:
    """Tests for calculate_backoff_delay function."""

    def test_first_attempt(self):
        """First attempt should use initial delay."""
        delay = calculate_backoff_delay(1, initial_delay_ms=500)
        assert delay == 500

    def test_second_attempt(self):
        """Second attempt should double delay."""
        delay = calculate_backoff_delay(2, initial_delay_ms=500)
        assert delay == 1000

    def test_third_attempt(self):
        """Third attempt should quadruple initial delay."""
        delay = calculate_backoff_delay(3, initial_delay_ms=500)
        assert delay == 2000

    def test_capped_at_max(self):
        """Delay should be capped at max_delay_ms."""
        delay = calculate_backoff_delay(10, initial_delay_ms=500, max_delay_ms=5000)
        assert delay == 5000

    def test_zero_attempt_returns_initial(self):
        """Zero attempt should return initial delay."""
        delay = calculate_backoff_delay(0, initial_delay_ms=500)
        assert delay == 500

    def test_custom_multiplier(self):
        """Should use custom multiplier."""
        delay = calculate_backoff_delay(2, initial_delay_ms=100, multiplier=3.0)
        assert delay == 300


class TestShouldRetry:
    """Tests for should_retry function."""

    def test_retryable_error_first_attempt(self):
        """First attempt of retryable error should retry."""
        should, delay = should_retry(TOO_MANY_REQUESTS, 1, max_retries=3)
        assert should is True
        assert delay > 0

    def test_retryable_error_exceeds_max(self):
        """Should not retry when exceeding max attempts."""
        should, delay = should_retry(TOO_MANY_REQUESTS, 4, max_retries=3)
        assert should is False
        assert delay == 0

    def test_non_retryable_error(self):
        """Non-retryable error should not retry."""
        should, delay = should_retry(NEW_ORDER_REJECTED, 1, max_retries=3)
        assert should is False
        assert delay == 0

    def test_rate_limit_extra_delay(self):
        """Rate limit errors should get extra delay."""
        should, rate_delay = should_retry(TOO_MANY_REQUESTS, 1, max_retries=3)
        _, network_delay = should_retry(DISCONNECTED, 1, max_retries=3)
        # Rate limit should have 2x delay
        assert rate_delay > network_delay

    def test_network_error_retry(self):
        """Network errors should be retryable."""
        should, delay = should_retry(DISCONNECTED, 1, max_retries=3)
        assert should is True
        assert delay > 0


class TestBinanceErrorCategory:
    """Tests for BinanceErrorCategory enum."""

    def test_category_values(self):
        """Enum should have expected values."""
        assert BinanceErrorCategory.UNKNOWN == 0
        assert BinanceErrorCategory.NETWORK == 1
        assert BinanceErrorCategory.RATE_LIMIT == 2
        assert BinanceErrorCategory.AUTHENTICATION == 3
        assert BinanceErrorCategory.VALIDATION == 4
        assert BinanceErrorCategory.BALANCE == 5
        assert BinanceErrorCategory.ORDER == 6
        assert BinanceErrorCategory.POSITION == 7
