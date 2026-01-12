"""Pipeline profiles for different trading scenarios.

Profiles allow selecting appropriate ML features based on strategy type:

- BASIC: Standard orchestration pipeline
- ML_LITE: + Regime Detection + Giller Sizing (80% benefit, 20% complexity)
- ML_FULL: + Walk-Forward + Triple Barrier + Meta-Labeling

Usage:
    from pipeline.profiles import PipelineProfile, create_pipeline

    # For rule-based strategies
    pipeline = create_pipeline(PipelineProfile.BASIC)

    # For ML-enhanced strategies
    pipeline = create_pipeline(PipelineProfile.ML_LITE)

    # For full ML pipeline
    pipeline = create_pipeline(PipelineProfile.ML_FULL)
"""

from pipeline.profiles.config import PipelineProfile, ProfileConfig
from pipeline.profiles.factory import create_pipeline, create_stages

__all__ = [
    "PipelineProfile",
    "ProfileConfig",
    "create_pipeline",
    "create_stages",
]
