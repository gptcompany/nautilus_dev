"""
Alpha-Evolve Core Infrastructure.

Provides foundational components for evolutionary strategy discovery:
- Patching: EVOLVE-BLOCK mutation system
- Store: SQLite persistence for strategies and metrics
- Config: Evolution parameter configuration
- Evaluator: Dynamic strategy evaluation via backtesting
- Templates: Evolvable strategy base classes
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

# Template exports (added in spec-008)
from scripts.alpha_evolve.templates import (
    BaseEvolveConfig,
    BaseEvolveStrategy,
    EquityPoint,
    MomentumEvolveConfig,
    MomentumEvolveStrategy,
)

__all__ += [
    # Templates
    "BaseEvolveConfig",
    "BaseEvolveStrategy",
    "EquityPoint",
    "MomentumEvolveConfig",
    "MomentumEvolveStrategy",
]

# Controller exports (added in spec-009)
from scripts.alpha_evolve.controller import (
    EvolutionController,
    EvolutionProgress,
    EvolutionResult,
    EvolutionStatus,
    ProgressEvent,
    ProgressEventType,
    StopCondition,
)

__all__ += [
    # Controller
    "EvolutionController",
    "EvolutionProgress",
    "EvolutionResult",
    "EvolutionStatus",
    "ProgressEvent",
    "ProgressEventType",
    "StopCondition",
]

# Mutator exports (added in spec-009)
from scripts.alpha_evolve.mutator import (
    LLMMutator,
    MockMutator,
    MutationRequest,
    MutationResponse,
    Mutator,
)

__all__ += [
    # Mutator
    "LLMMutator",
    "MockMutator",
    "MutationRequest",
    "MutationResponse",
    "Mutator",
]
