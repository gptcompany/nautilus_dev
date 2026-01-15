"""Pipeline profile configuration.

Defines profile levels and their feature sets.
"""

from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any

import yaml


class PipelineProfile(IntEnum):
    """Pipeline profile levels.

    Ordered by complexity - higher profiles include all features from lower profiles.

    Attributes:
        BASIC: Standard orchestration (DATA → ALPHA → RISK → EXECUTION → MONITORING)
        ML_LITE: Adds Regime Detection + Giller Sizing
        ML_FULL: Adds Walk-Forward + Triple Barrier + Meta-Labeling
    """

    BASIC = 1
    ML_LITE = 2
    ML_FULL = 3


@dataclass
class RegimeConfig:
    """Configuration for regime detection."""

    enabled: bool = True
    hmm_n_regimes: int = 3
    gmm_n_clusters: int = 3
    lookback_bars: int = 252
    refit_interval: int = 20


@dataclass
class SizingConfig:
    """Configuration for position sizing."""

    method: str = "giller"  # "linear", "giller", "kelly"
    giller_exponent: float = 0.5
    max_position_pct: float = 10.0
    regime_weight_enabled: bool = True


@dataclass
class WalkForwardConfig:
    """Configuration for walk-forward validation."""

    enabled: bool = True
    train_window: int = 252  # ~1 year of daily bars
    test_window: int = 63  # ~3 months
    step_size: int = 21  # ~1 month
    embargo_size: int = 5  # Gap between train/test
    min_windows: int = 4


@dataclass
class TripleBarrierConfig:
    """Configuration for triple barrier labeling."""

    enabled: bool = True
    take_profit_atr: float = 2.0
    stop_loss_atr: float = 2.0
    max_holding_bars: int = 20
    atr_period: int = 14


@dataclass
class MetaLabelConfig:
    """Configuration for meta-labeling."""

    enabled: bool = True
    model_type: str = "random_forest"  # "random_forest", "xgboost", "lightgbm"
    min_confidence: float = 0.5
    retrain_interval: int = 100


@dataclass
class ProfileConfig:
    """Complete configuration for a pipeline profile.

    Attributes:
        profile: The profile level
        regime: Regime detection config (ML_LITE+)
        sizing: Position sizing config (ML_LITE+)
        walk_forward: Walk-forward validation config (ML_FULL)
        triple_barrier: Triple barrier labeling config (ML_FULL)
        meta_label: Meta-labeling config (ML_FULL)
        custom: Additional custom parameters
    """

    profile: PipelineProfile = PipelineProfile.BASIC

    # ML_LITE features
    regime: RegimeConfig = field(default_factory=RegimeConfig)
    sizing: SizingConfig = field(default_factory=SizingConfig)

    # ML_FULL features
    walk_forward: WalkForwardConfig = field(default_factory=WalkForwardConfig)
    triple_barrier: TripleBarrierConfig = field(default_factory=TripleBarrierConfig)
    meta_label: MetaLabelConfig = field(default_factory=MetaLabelConfig)

    # Custom overrides
    custom: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Disable features not included in profile."""
        if self.profile < PipelineProfile.ML_LITE:
            self.regime.enabled = False
            self.sizing.method = "linear"

        if self.profile < PipelineProfile.ML_FULL:
            self.walk_forward.enabled = False
            self.triple_barrier.enabled = False
            self.meta_label.enabled = False

    @classmethod
    def from_yaml(cls, path: Path) -> "ProfileConfig":
        """Load configuration from YAML file.

        Args:
            path: Path to YAML configuration file

        Returns:
            ProfileConfig instance
        """
        with open(path) as f:
            data = yaml.safe_load(f)

        profile = PipelineProfile[data.get("profile", "BASIC").upper()]

        return cls(
            profile=profile,
            regime=RegimeConfig(**data.get("regime", {})),
            sizing=SizingConfig(**data.get("sizing", {})),
            walk_forward=WalkForwardConfig(**data.get("walk_forward", {})),
            triple_barrier=TripleBarrierConfig(**data.get("triple_barrier", {})),
            meta_label=MetaLabelConfig(**data.get("meta_label", {})),
            custom=data.get("custom", {}),
        )

    def to_yaml(self, path: Path) -> None:
        """Save configuration to YAML file.

        Args:
            path: Path to save YAML configuration
        """
        from dataclasses import asdict

        data = {
            "profile": self.profile.name,
            "regime": asdict(self.regime),
            "sizing": asdict(self.sizing),
            "walk_forward": asdict(self.walk_forward),
            "triple_barrier": asdict(self.triple_barrier),
            "meta_label": asdict(self.meta_label),
            "custom": self.custom,
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Preset configurations
PROFILE_PRESETS: dict[PipelineProfile, ProfileConfig] = {
    PipelineProfile.BASIC: ProfileConfig(profile=PipelineProfile.BASIC),
    PipelineProfile.ML_LITE: ProfileConfig(profile=PipelineProfile.ML_LITE),
    PipelineProfile.ML_FULL: ProfileConfig(profile=PipelineProfile.ML_FULL),
}


def get_preset(profile: PipelineProfile) -> ProfileConfig:
    """Get preset configuration for a profile.

    Args:
        profile: The profile level

    Returns:
        ProfileConfig with default settings for that profile
    """
    return PROFILE_PRESETS[profile]
