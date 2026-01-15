"""Pipeline factory for creating profile-specific pipelines.

Creates stage configurations based on selected profile, integrating
ML features from strategies/common/ modules.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.core.loop import PipelineLoop
from pipeline.hitl.approval import ApprovalGate
from pipeline.hitl.notifications import create_notification_service
from pipeline.profiles.config import (
    PipelineProfile,
    ProfileConfig,
    get_preset,
)
from pipeline.stages.alpha import AlphaStage
from pipeline.stages.base import AbstractStage
from pipeline.stages.data import DataStage
from pipeline.stages.execution import ExecutionStage
from pipeline.stages.monitoring import MonitoringStage
from pipeline.stages.risk import RiskStage

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class ProfiledAlphaStage(AlphaStage):
    """Alpha stage with profile-specific ML features."""

    def __init__(self, config: ProfileConfig):
        """Initialize with profile configuration.

        Args:
            config: Profile configuration
        """
        super().__init__()
        self.profile_config = config
        self._regime_manager = None
        self._walk_forward = None
        self._triple_barrier = None
        self._meta_model = None

        self._init_ml_features()

    def _init_ml_features(self) -> None:
        """Initialize ML features based on profile."""
        config = self.profile_config

        # ML_LITE: Regime Detection
        if config.regime.enabled:
            try:
                from strategies.common.regime_detection import RegimeManager
                from strategies.common.regime_detection.config import RegimeConfig as RCfg

                regime_cfg = RCfg(
                    hmm_n_regimes=config.regime.hmm_n_regimes,
                    gmm_n_clusters=config.regime.gmm_n_clusters,
                    lookback_bars=config.regime.lookback_bars,
                )
                self._regime_manager = RegimeManager(regime_cfg)
                logger.info("Regime detection enabled (HMM + GMM)")
            except ImportError as e:
                logger.warning(f"Regime detection unavailable: {e}")

        # ML_FULL: Walk-Forward Validation
        if config.walk_forward.enabled:
            try:
                from strategies.common.meta_learning import WalkForwardSplitter
                from strategies.common.meta_learning.config import (
                    WalkForwardConfig as WFCfg,
                )

                wf_cfg = WFCfg(
                    train_window=config.walk_forward.train_window,
                    test_window=config.walk_forward.test_window,
                    step_size=config.walk_forward.step_size,
                    embargo_size=config.walk_forward.embargo_size,
                )
                self._walk_forward = WalkForwardSplitter(wf_cfg)
                logger.info("Walk-forward validation enabled")
            except ImportError as e:
                logger.warning(f"Walk-forward validation unavailable: {e}")

        # ML_FULL: Triple Barrier Labeling
        if config.triple_barrier.enabled:
            try:
                from strategies.common.labeling import TripleBarrierLabeler
                from strategies.common.labeling.config import (
                    TripleBarrierConfig as TBCfg,
                )

                tb_cfg = TBCfg(
                    take_profit_atr=config.triple_barrier.take_profit_atr,
                    stop_loss_atr=config.triple_barrier.stop_loss_atr,
                    max_holding_bars=config.triple_barrier.max_holding_bars,
                    atr_period=config.triple_barrier.atr_period,
                )
                self._triple_barrier = TripleBarrierLabeler(tb_cfg)
                logger.info("Triple barrier labeling enabled")
            except ImportError as e:
                logger.warning(f"Triple barrier labeling unavailable: {e}")

        # ML_FULL: Meta-Model
        if config.meta_label.enabled:
            try:
                from strategies.common.meta_learning import MetaModel
                from strategies.common.meta_learning.config import MetaModelConfig

                meta_cfg = MetaModelConfig(
                    model_type=config.meta_label.model_type,
                    min_confidence=config.meta_label.min_confidence,
                )
                self._meta_model = MetaModel(meta_cfg)
                logger.info("Meta-labeling enabled")
            except ImportError as e:
                logger.warning(f"Meta-labeling unavailable: {e}")

    @property
    def regime_manager(self):
        """Get regime manager if available."""
        return self._regime_manager

    @property
    def walk_forward(self):
        """Get walk-forward splitter if available."""
        return self._walk_forward

    @property
    def triple_barrier(self):
        """Get triple barrier labeler if available."""
        return self._triple_barrier

    @property
    def meta_model(self):
        """Get meta-model if available."""
        return self._meta_model


class ProfiledRiskStage(RiskStage):
    """Risk stage with profile-specific position sizing."""

    def __init__(self, config: ProfileConfig):
        """Initialize with profile configuration.

        Args:
            config: Profile configuration
        """
        super().__init__()
        self.profile_config = config
        self._sizer = None

        self._init_sizing()

    def _init_sizing(self) -> None:
        """Initialize position sizing based on profile."""
        config = self.profile_config

        if config.sizing.method == "giller":
            try:
                from strategies.common.position_sizing import GillerSizer
                from strategies.common.position_sizing.config import GillerConfig

                giller_cfg = GillerConfig(
                    exponent=config.sizing.giller_exponent,
                    max_position_pct=config.sizing.max_position_pct,
                )
                self._sizer = GillerSizer(giller_cfg)
                logger.info("Giller sub-linear sizing enabled")
            except ImportError as e:
                logger.warning(f"Giller sizing unavailable: {e}")

        elif config.sizing.method == "integrated":
            try:
                from strategies.common.position_sizing import IntegratedSizer
                from strategies.common.position_sizing.config import IntegratedConfig

                int_cfg = IntegratedConfig(
                    max_position_pct=config.sizing.max_position_pct,
                    regime_weight_enabled=config.sizing.regime_weight_enabled,
                )
                self._sizer = IntegratedSizer(int_cfg)
                logger.info("Integrated sizing enabled")
            except ImportError as e:
                logger.warning(f"Integrated sizing unavailable: {e}")

    @property
    def sizer(self):
        """Get position sizer if available."""
        return self._sizer


def create_stages(config: ProfileConfig) -> list[AbstractStage]:
    """Create pipeline stages based on profile configuration.

    Args:
        config: Profile configuration

    Returns:
        List of configured pipeline stages
    """
    stages: list[AbstractStage] = []

    # DATA stage - always basic
    stages.append(DataStage())

    # ALPHA stage - profile-dependent
    if config.profile >= PipelineProfile.ML_LITE:
        stages.append(ProfiledAlphaStage(config))
    else:
        stages.append(AlphaStage())

    # RISK stage - profile-dependent
    if config.profile >= PipelineProfile.ML_LITE:
        stages.append(ProfiledRiskStage(config))
    else:
        stages.append(RiskStage())

    # EXECUTION stage - always basic
    stages.append(ExecutionStage())

    # MONITORING stage - always basic
    stages.append(MonitoringStage())

    logger.info(f"Created {len(stages)} stages for profile {config.profile.name}")

    return stages


def create_pipeline(
    profile: PipelineProfile | ProfileConfig,
    checkpoint_dir: Path | None = None,
    notification_webhook: str | None = None,
) -> PipelineLoop:
    """Create a complete pipeline for the specified profile.

    Args:
        profile: Profile level or full configuration
        checkpoint_dir: Directory for checkpoints (optional)
        notification_webhook: Discord webhook URL for notifications (optional)

    Returns:
        Configured PipelineLoop instance

    Example:
        >>> from pipeline.profiles import PipelineProfile, create_pipeline
        >>>
        >>> # Simple usage with preset
        >>> pipeline = create_pipeline(PipelineProfile.ML_LITE)
        >>>
        >>> # Custom configuration
        >>> from pipeline.profiles.config import ProfileConfig
        >>> config = ProfileConfig(profile=PipelineProfile.ML_FULL)
        >>> config.regime.hmm_n_regimes = 4
        >>> pipeline = create_pipeline(config)
    """
    # Get configuration
    if isinstance(profile, PipelineProfile):
        config = get_preset(profile)
    else:
        config = profile

    # Create stages
    stages = create_stages(config)

    # Create notification service if webhook provided
    notification_service = None
    if notification_webhook:
        notification_service = create_notification_service(notification_webhook)

    # Create approval gate
    approval_gate = ApprovalGate(notification_service)

    # Create pipeline loop
    pipeline = PipelineLoop(
        stages=stages,
        approval_gate=approval_gate,
        checkpoint_dir=checkpoint_dir or Path("./checkpoints"),
        auto_checkpoint=True,
    )

    logger.info(f"Pipeline created with profile {config.profile.name}")

    return pipeline
