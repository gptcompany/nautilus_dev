"""Walk-Forward Validation module for Alpha-Evolve.

This module provides walk-forward validation for evolved strategies
to prevent overfitting and ensure robustness before live deployment.

Public API:
    - WalkForwardConfig: Configuration for validation runs
    - WalkForwardValidator: Main validator class
    - WalkForwardResult: Complete validation results
    - Window, WindowMetrics, WindowResult: Data models
    - generate_report: Markdown report generation
    - export_json: JSON export for programmatic use
"""

from scripts.alpha_evolve.walk_forward.config import WalkForwardConfig
from scripts.alpha_evolve.walk_forward.models import (
    WalkForwardResult,
    Window,
    WindowMetrics,
    WindowResult,
)
from scripts.alpha_evolve.walk_forward.report import export_json, generate_report
from scripts.alpha_evolve.walk_forward.validator import WalkForwardValidator

__all__ = [
    "WalkForwardConfig",
    "WalkForwardValidator",
    "WalkForwardResult",
    "Window",
    "WindowMetrics",
    "WindowResult",
    "generate_report",
    "export_json",
]
