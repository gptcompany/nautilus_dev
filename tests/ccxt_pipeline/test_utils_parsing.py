"""Unit tests for parsing utilities."""


from scripts.ccxt_pipeline.utils.parsing import safe_float, safe_int, safe_str


class TestSafeFloat:
    """Tests for safe_float function."""

    def test_valid_float(self) -> None:
        """Test conversion of valid float."""
        assert safe_float(123.45) == 123.45

    def test_valid_int(self) -> None:
        """Test conversion of int to float."""
        assert safe_float(123) == 123.0

    def test_valid_string(self) -> None:
        """Test conversion of numeric string."""
        assert safe_float("123.45") == 123.45

    def test_none_returns_default(self) -> None:
        """Test None returns default value."""
        assert safe_float(None) == 0.0
        assert safe_float(None, -1.0) == -1.0

    def test_invalid_string_returns_default(self) -> None:
        """Test invalid string returns default."""
        assert safe_float("invalid") == 0.0
        assert safe_float("invalid", -1.0) == -1.0

    def test_empty_string_returns_default(self) -> None:
        """Test empty string returns default."""
        assert safe_float("") == 0.0

    def test_dict_get_with_explicit_none(self) -> None:
        """Test handling of dict.get() returning explicit None.

        This is the bug we're fixing: data.get("key", 0) returns None
        when key exists with value None, not the default 0.
        """
        data = {"openInterestAmount": None, "openInterestValue": 12345.0}

        # Old pattern would crash: float(data.get("openInterestAmount", 0))
        # because data.get() returns None, not 0

        # New pattern works:
        assert safe_float(data.get("openInterestAmount")) == 0.0
        assert safe_float(data.get("openInterestValue")) == 12345.0
        assert safe_float(data.get("missing_key")) == 0.0

    def test_nan_returns_default(self) -> None:
        """Test NaN returns default (prevents silent bugs in trading calculations)."""
        import math

        assert safe_float("nan") == 0.0
        assert safe_float(float("nan")) == 0.0
        assert safe_float(float("nan"), -1.0) == -1.0
        # Verify returned value is finite
        assert math.isfinite(safe_float("nan"))

    def test_inf_returns_default(self) -> None:
        """Test Inf returns default (prevents overflow issues in trading)."""
        import math

        assert safe_float("inf") == 0.0
        assert safe_float("-inf") == 0.0
        assert safe_float(float("inf")) == 0.0
        assert safe_float(float("-inf")) == 0.0
        assert safe_float("inf", -1.0) == -1.0
        # Verify returned value is finite
        assert math.isfinite(safe_float("inf"))

    def test_overflow_to_inf_returns_default(self) -> None:
        """Test values that overflow to inf return default."""
        # 1e309 overflows to inf
        assert safe_float("1e309") == 0.0
        assert safe_float("-1e309") == 0.0


class TestSafeInt:
    """Tests for safe_int function."""

    def test_valid_int(self) -> None:
        """Test conversion of valid int."""
        assert safe_int(123) == 123

    def test_valid_float(self) -> None:
        """Test conversion of float to int (truncates)."""
        assert safe_int(123.9) == 123

    def test_valid_string(self) -> None:
        """Test conversion of numeric string."""
        assert safe_int("123") == 123

    def test_float_string(self) -> None:
        """Test conversion of float string to int."""
        assert safe_int("123.9") == 123

    def test_none_returns_default(self) -> None:
        """Test None returns default value."""
        assert safe_int(None) == 0
        assert safe_int(None, -1) == -1

    def test_invalid_string_returns_default(self) -> None:
        """Test invalid string returns default."""
        assert safe_int("invalid") == 0

    def test_nan_returns_default(self) -> None:
        """Test NaN returns default."""
        assert safe_int("nan") == 0
        assert safe_int(float("nan")) == 0
        assert safe_int(float("nan"), -1) == -1

    def test_inf_returns_default(self) -> None:
        """Test Inf returns default (int(inf) would raise OverflowError)."""
        assert safe_int("inf") == 0
        assert safe_int("-inf") == 0
        assert safe_int(float("inf")) == 0
        assert safe_int(float("-inf")) == 0
        assert safe_int("inf", -1) == -1


class TestSafeStr:
    """Tests for safe_str function."""

    def test_valid_string(self) -> None:
        """Test string passthrough."""
        assert safe_str("hello") == "hello"

    def test_int_to_string(self) -> None:
        """Test int conversion to string."""
        assert safe_str(123) == "123"

    def test_float_to_string(self) -> None:
        """Test float conversion to string."""
        assert safe_str(123.45) == "123.45"

    def test_none_returns_default(self) -> None:
        """Test None returns default value."""
        assert safe_str(None) == ""
        assert safe_str(None, "N/A") == "N/A"
