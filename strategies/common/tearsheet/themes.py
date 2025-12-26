"""
Custom theme registration for NautilusTrader tearsheets.

This module provides project-specific themes that extend NautilusTrader's
built-in theme system.

Built-in Themes
---------------
NautilusTrader provides 4 built-in themes:
- plotly_white: Clean light theme (default)
- plotly_dark: Dark background
- nautilus: Light with NautilusTrader branding
- nautilus_dark: Dark with NautilusTrader branding

Custom Theme
------------
- nautilus_dev: Project-specific theme with custom brand colors
"""

from __future__ import annotations

import logging

_logger = logging.getLogger(__name__)

# Theme name constant
NAUTILUS_DEV_THEME = "nautilus_dev"

# Project brand colors
NAUTILUS_DEV_COLORS: dict[str, str] = {
    "primary": "#1a365d",  # Navy blue (project branding)
    "secondary": "#2d4a6f",  # Lighter navy
    "positive": "#22c55e",  # Green for profits
    "negative": "#ef4444",  # Red for losses
    "neutral": "#6b7280",  # Gray for neutral
    "background": "#ffffff",  # White background
    "paper": "#f9fafb",  # Slight off-white for cards
    "grid": "#e5e7eb",  # Light gray grid lines
    "text": "#111827",  # Dark text
    "text_muted": "#6b7280",  # Muted text
    # Table colors
    "table_header": "#1a365d",
    "table_section": "#f3f4f6",
    "table_row_odd": "#f9fafb",
    "table_row_even": "#ffffff",
    "table_text": "#111827",
    "table_text_header": "#ffffff",
}

# Track registration state
_theme_registered = False


def register_nautilus_dev_theme() -> None:
    """
    Register the nautilus_dev custom theme.

    This function should be called once at application startup.
    Subsequent calls are no-ops.

    The theme is based on plotly_white with custom brand colors.

    Example
    -------
    >>> from strategies.common.tearsheet.themes import register_nautilus_dev_theme
    >>> register_nautilus_dev_theme()
    >>> # Now use the theme
    >>> config = TearsheetConfig(theme="nautilus_dev")
    """
    global _theme_registered

    if _theme_registered:
        _logger.debug("nautilus_dev theme already registered")
        return

    try:
        from nautilus_trader.analysis.themes import register_theme

        register_theme(
            name=NAUTILUS_DEV_THEME,
            template="plotly_white",
            colors=NAUTILUS_DEV_COLORS,
        )
        _theme_registered = True
        _logger.info(f"Registered custom theme: {NAUTILUS_DEV_THEME}")

    except ImportError as e:
        _logger.warning(f"Could not import theme registration: {e}")
    except Exception as e:
        _logger.error(f"Failed to register theme: {e}")


def get_theme_colors(theme: str = NAUTILUS_DEV_THEME) -> dict[str, str]:
    """
    Get color palette for a theme.

    Parameters
    ----------
    theme : str
        Theme name.

    Returns
    -------
    dict[str, str]
        Color palette dictionary.
    """
    if theme == NAUTILUS_DEV_THEME:
        return NAUTILUS_DEV_COLORS.copy()

    # Return defaults for other themes
    return {
        "primary": "#636efa",
        "positive": "#00cc96",
        "negative": "#ef553b",
        "neutral": "#636efa",
    }


def is_theme_registered(theme: str = NAUTILUS_DEV_THEME) -> bool:
    """
    Check if a theme is registered.

    Parameters
    ----------
    theme : str
        Theme name.

    Returns
    -------
    bool
        True if theme is registered.
    """
    if theme == NAUTILUS_DEV_THEME:
        return _theme_registered
    return True  # Built-in themes are always available


def verify_native_themes() -> dict[str, bool]:
    """
    Verify that all native themes are available.

    Returns
    -------
    dict[str, bool]
        Theme name to availability mapping.
    """
    native_themes = [
        "plotly_white",
        "plotly_dark",
        "nautilus",
        "nautilus_dark",
    ]

    results = {}
    for theme in native_themes:
        try:
            # Try to use the theme in a config
            from nautilus_trader.analysis import TearsheetConfig

            TearsheetConfig(theme=theme)
            results[theme] = True
        except Exception:
            results[theme] = False

    return results
