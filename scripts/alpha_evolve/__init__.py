"""
Alpha-Evolve Core Infrastructure.

Provides foundational components for evolutionary strategy discovery:
- Patching: EVOLVE-BLOCK mutation system
- Store: SQLite persistence for strategies and metrics
- Config: Evolution parameter configuration
- Evaluator: Dynamic strategy evaluation via backtesting
"""

__version__ = "0.1.0"

# Patching exports
from scripts.alpha_evolve.patching import (
    BLOCK_RE,
    apply_patch,
    extract_blocks,
    validate_syntax,
)

# Store exports
from scripts.alpha_evolve.store import (
    FitnessMetrics,
    Program,
    ProgramStore,
)

# Config exports
from scripts.alpha_evolve.config import EvolutionConfig

# Evaluator exports
from scripts.alpha_evolve.evaluator import (
    BacktestConfig,
    EvaluationRequest,
    EvaluationResult,
    StrategyEvaluator,
)

__all__ = [
    # Patching
    "BLOCK_RE",
    "apply_patch",
    "extract_blocks",
    "validate_syntax",
    # Store
    "FitnessMetrics",
    "Program",
    "ProgramStore",
    # Config
    "EvolutionConfig",
    # Evaluator
    "BacktestConfig",
    "EvaluationRequest",
    "EvaluationResult",
    "StrategyEvaluator",
]
