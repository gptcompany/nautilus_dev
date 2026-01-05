"""Baseline Validation Framework for NautilusTrader.

This module provides rigorous validation comparing adaptive position sizing
(SOPS+Giller+Thompson) against simple baselines (Fixed 2%, Buy & Hold).

Based on PMW (Prove Me Wrong) philosophy:
    "Cerca attivamente disconferme, non conferme"

Key Reference:
    DeMiguel et al. (2009) - "1/N beats 14 optimization models OOS"

Components:
    - sizers: ContenderSizer implementations (Fixed, BuyAndHold, Adaptive)
    - registry: Contender discovery and registration
    - baseline_strategy: Generic strategy wrapper for fair comparison
    - comparison_validator: Multi-contender walk-forward validation
    - comparison_metrics: Relative performance metrics
    - verdict: GO/WAIT/STOP decision logic
    - report: Markdown and JSON report generation
    - cli: Command-line interface

Usage:
    >>> from scripts.baseline_validation import ComparisonValidator, BaselineValidationConfig
    >>> config = BaselineValidationConfig.default()
    >>> validator = ComparisonValidator(config)
    >>> result = validator.run_mock()  # or validator.run() for real backtest
    >>> from scripts.baseline_validation import create_report_from_validation_run
    >>> report = create_report_from_validation_run(result)
    >>> print(report.verdict)  # GO, WAIT, or STOP
"""

__version__ = "0.1.0"
__author__ = "NautilusTrader Team"

# Core sizers
from scripts.baseline_validation.sizers import (
    ContenderSizer,
    FixedFractionalSizer,
    BuyAndHoldSizer,
    AdaptiveSizer,
    create_sizer,
)

# Registry
from scripts.baseline_validation.registry import (
    ContenderRegistry,
    get_default_contenders,
)

# Configuration
from scripts.baseline_validation.config_models import (
    BaselineValidationConfig,
    ValidationConfig,
    SuccessCriteriaConfig,
    ContenderConfig,
)

# Validation
from scripts.baseline_validation.comparison_validator import (
    ComparisonValidator,
    ContenderResult,
    ValidationRun,
)

# Metrics
from scripts.baseline_validation.comparison_metrics import (
    MultiContenderComparison,
    ComparisonResult,
    ContenderMetrics,
)

# Verdict
from scripts.baseline_validation.verdict import (
    determine_verdict,
    calculate_confidence,
    generate_recommendation,
)
from scripts.baseline_validation.report_models import Verdict

# Reports
from scripts.baseline_validation.report import (
    create_report_from_validation_run,
    generate_markdown_report,
    format_comparison_table,
    export_to_json,
)
from scripts.baseline_validation.report_models import (
    ValidationReport,
    ContenderSummary,
    VerdictDetails,
)

# Strategy
from scripts.baseline_validation.baseline_strategy import BaselineStrategy

__all__ = [
    # Core sizers
    "ContenderSizer",
    "FixedFractionalSizer",
    "BuyAndHoldSizer",
    "AdaptiveSizer",
    "create_sizer",
    # Registry
    "ContenderRegistry",
    "get_default_contenders",
    # Configuration
    "BaselineValidationConfig",
    "ValidationConfig",
    "SuccessCriteriaConfig",
    "ContenderConfig",
    # Validation
    "ComparisonValidator",
    "ContenderResult",
    "ValidationRun",
    # Metrics
    "MultiContenderComparison",
    "ComparisonResult",
    "ContenderMetrics",
    # Verdict
    "Verdict",
    "determine_verdict",
    "calculate_confidence",
    "generate_recommendation",
    # Reports
    "ValidationReport",
    "ContenderSummary",
    "VerdictDetails",
    "create_report_from_validation_run",
    "generate_markdown_report",
    "format_comparison_table",
    "export_to_json",
    # Strategy
    "BaselineStrategy",
]
