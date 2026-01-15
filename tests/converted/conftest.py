"""Converted tests configuration.

Skip all tests if nautilus_trader is not installed.
"""

import pytest

try:
    import nautilus_trader  # noqa: F401
except ImportError:
    pytest.skip("nautilus_trader not installed", allow_module_level=True)
