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
    >>> from scripts.baseline_validation import ComparisonValidator
    >>> validator = ComparisonValidator(config)
    >>> result = validator.validate()
    >>> print(result.verdict)  # GO, WAIT, or STOP
"""

__version__ = "0.1.0"
__author__ = "NautilusTrader Team"

# Lazy imports to avoid circular dependencies
__all__ = [
    "ContenderSizer",
    "FixedFractionalSizer",
    "BuyAndHoldSizer",
    "AdaptiveSizer",
    "ContenderRegistry",
    "BaselineStrategy",
    "ComparisonValidator",
    "ComparisonMetrics",
    "Verdict",
    "ReportGenerator",
]
