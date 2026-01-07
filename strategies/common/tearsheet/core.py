"""
Core tearsheet wrapper for NautilusTrader.

This module provides the main generate_tearsheet() function that wraps
NautilusTrader's native create_tearsheet() with edge case handling.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nautilus_trader.analysis import TearsheetConfig
    from nautilus_trader.backtest.engine import BacktestEngine

_logger = logging.getLogger(__name__)


def generate_tearsheet(
    engine: BacktestEngine,
    output_path: str = "tearsheet.html",
    config: TearsheetConfig | None = None,
    **kwargs,
) -> str:
    """
    Generate tearsheet with edge case handling.

    This is a wrapper around NautilusTrader's native `create_tearsheet()`
    that adds edge case detection, warning display, and performance optimizations.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine with portfolio data.
    output_path : str, optional
        Output HTML file path. Default "tearsheet.html".
    config : TearsheetConfig, optional
        Tearsheet configuration. Uses defaults if None.
    **kwargs
        Additional arguments passed to native create_tearsheet().

    Returns
    -------
    str
        Path to generated HTML file.

    Example
    -------
    >>> from strategies.common.tearsheet import generate_tearsheet
    >>> result = generate_tearsheet(engine, output_path="my_backtest.html")
    >>> print(f"Tearsheet saved to: {result}")
    """
    from strategies.common.tearsheet.edge_cases import (
        check_edge_cases,
        should_use_scattergl,
    )

    # Run edge case checks
    warnings = check_edge_cases(engine)

    # Log any detected warnings
    for warning in warnings:
        if warning.severity.value == "error":
            _logger.error(str(warning))
        elif warning.severity.value == "warning":
            _logger.warning(str(warning))
        else:
            _logger.info(str(warning))

    # Check if we should use ScatterGL for large datasets
    use_scattergl = should_use_scattergl(engine)
    if use_scattergl:
        _logger.info("Using ScatterGL for improved performance with large dataset")

    # Call native tearsheet creation
    _create_tearsheet_native(engine, output_path, config, **kwargs)

    _logger.info(f"Tearsheet generated: {output_path}")
    return output_path


def _create_tearsheet_native(
    engine: BacktestEngine,
    output_path: str,
    config: TearsheetConfig | None = None,
    **kwargs,
) -> None:
    """
    Call NautilusTrader's native create_tearsheet function.

    This is separated for easier mocking in tests.

    Parameters
    ----------
    engine : BacktestEngine
        Completed backtest engine.
    output_path : str
        Output HTML file path.
    config : TearsheetConfig, optional
        Tearsheet configuration.
    **kwargs
        Additional arguments.
    """
    try:
        from nautilus_trader.analysis import TearsheetConfig
        from nautilus_trader.analysis.tearsheet import create_tearsheet

        # Use default config if not provided
        if config is None:
            config = TearsheetConfig()

        # Create the tearsheet using native API
        create_tearsheet(
            engine=engine,
            output_path=output_path,
            config=config,
            **kwargs,
        )
    except ImportError as e:
        _logger.error(f"Could not import tearsheet module: {e}")
        _logger.error("Ensure NautilusTrader is installed with visualization extra")
        raise
    except Exception as e:
        _logger.error(f"Error creating tearsheet: {e}")
        raise
