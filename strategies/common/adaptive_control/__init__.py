# Adaptive Control Trading Framework
# DSP + Control Theory for algorithmic trading
#
# Philosophy: Probability, Non-linearity, Non-parametric
# NO FIXED PARAMETERS - Adaptive to data
#
# THE SYNTHESIS:
#
#   META-CONTROLLER (Il Cervello)
#        │
#        ├── SystemHealthMonitor (Polyvagal: Ventral/Sympathetic/Dorsal)
#        ├── SpectralRegimeDetector (Non-parametric market regime)
#        ├── PIDDrawdownController (Dynamic risk control)
#        │
#        └── TRIGGERS Alpha-Evolve when DISSONANT
#            → Evolves new strategies to match new regime
#
# INTEGRATES WITH:
# - alpha_evolve (specs 006-010): Strategy evolution
# - position_sizing/giller_sizing.py: Non-linear sizing
# - meta_learning/meta_model.py: RandomForest confidence
# - regime_detection/regime_manager.py: HMM + GMM + Spectral

from .spectral_regime import SpectralRegimeDetector, MarketRegime
from .system_health import SystemHealthMonitor, HealthState
from .pid_drawdown import PIDDrawdownController, SimpleDrawdownScaler
from .meta_controller import MetaController, MetaState, SystemState, MarketHarmony
from .regime_integration import (
    EnhancedRegimeManager,
    CombinedRegime,
    EnhancedRegimeResult,
)
from .dsp_filters import (
    IIRLowPass,
    IIRHighPass,
    RecursiveVariance,
    KalmanFilter1D,
    LMSAdaptiveFilter,
    IIRRegimeDetector,
    DSPRegimeDetector,
)
from .alpha_evolve_bridge import (
    AlphaEvolveBridge,
    AdaptiveSurvivalSystem,
    EvolutionRequest,
    EvolutionTrigger,
    EvolutionConfig,
)

# NOTE: universal_laws removed (2026-01-05) - PMW validation found no academic evidence
# for Fibonacci/wave physics in trading. See CLAUDE.md for details.
from .vibration_analysis import (
    VibrationAnalyzer,
    VibrationMode,
    ResonanceEvent,
    HarmonicRatioAnalyzer,
    DigitalRootAnalyzer,
)
from .flow_physics import (
    MarketFlowAnalyzer,
    FlowState,
    WaveEquationAnalyzer,
    InformationDiffusion,
)
from .multi_dimensional_regime import (
    MultiDimensionalRegimeDetector,
    MultiDimensionalResult,
    ConsensusRegime,
    DimensionResult,
    create_multi_regime_detector,
)
from .information_theory import (
    EntropyEstimator,
    MutualInformationEstimator,
    WienerFilter,
    InformationBasedRiskManager,
    InformationState,
    OptimalSamplingAnalyzer,
)
from .particle_portfolio import (
    ParticlePortfolio,
    ThompsonSelector,
    BayesianEnsemble,
    Particle,
    PortfolioState,
)
from .correlation_tracker import (
    OnlineCorrelationMatrix,
    OnlineStats,
    CorrelationMetrics,
    calculate_covariance_penalty,
)
from .meta_portfolio import (
    MetaPortfolio,
    BacktestMatrix,
    BacktestResult,
    SystemConfig,
    create_meta_portfolio_from_backtest,
)
from .luck_skill import (
    LuckQuantifier,
    TrackRecordAnalyzer,
    SkillAssessment,
)
from .sops_sizing import (
    SOPS,
    TapeSpeed,
    GillerScaler,
    SOPSGillerSizer,
    AdaptiveKEstimator,
    SOPSState,
    TapeSpeedState,
    create_sops_sizer,
)

__all__ = [
    # Core detectors (FFT-based, accurate but slower)
    "SpectralRegimeDetector",
    "MarketRegime",
    # System health
    "SystemHealthMonitor",
    "HealthState",
    # Risk control
    "PIDDrawdownController",
    "SimpleDrawdownScaler",
    # Meta system (THE BRAIN)
    "MetaController",
    "MetaState",
    "SystemState",
    "MarketHarmony",
    # Regime integration
    "EnhancedRegimeManager",
    "CombinedRegime",
    "EnhancedRegimeResult",
    # DSP Filters (O(1) per sample - FAST)
    "IIRLowPass",
    "IIRHighPass",
    "RecursiveVariance",
    "KalmanFilter1D",
    "LMSAdaptiveFilter",
    "IIRRegimeDetector",
    "DSPRegimeDetector",
    # Alpha-Evolve Bridge (strategy evolution)
    "AlphaEvolveBridge",
    "AdaptiveSurvivalSystem",
    "EvolutionRequest",
    "EvolutionTrigger",
    "EvolutionConfig",
    # NOTE: Universal Laws removed (2026-01-05) - PMW validation
    # Vibration Analysis (cycles, harmonics)
    "VibrationAnalyzer",
    "VibrationMode",
    "ResonanceEvent",
    "HarmonicRatioAnalyzer",
    "DigitalRootAnalyzer",
    # Flow Physics (markets as fluid systems)
    "MarketFlowAnalyzer",
    "FlowState",
    "WaveEquationAnalyzer",
    "InformationDiffusion",
    # Multi-Dimensional Regime (consensus from multiple views)
    "MultiDimensionalRegimeDetector",
    "MultiDimensionalResult",
    "ConsensusRegime",
    "DimensionResult",
    "create_multi_regime_detector",
    # Information Theory (entropy, SNR, risk)
    "EntropyEstimator",
    "MutualInformationEstimator",
    "WienerFilter",
    "InformationBasedRiskManager",
    "InformationState",
    "OptimalSamplingAnalyzer",
    # Particle-based Portfolio Selection
    "ParticlePortfolio",
    "ThompsonSelector",
    "BayesianEnsemble",
    "Particle",
    "PortfolioState",
    # CSRC Correlation Tracking (Spec 031)
    "OnlineCorrelationMatrix",
    "OnlineStats",
    "CorrelationMetrics",
    "calculate_covariance_penalty",
    # Meta-Portfolio (backtest matrix + production ensemble)
    "MetaPortfolio",
    "BacktestMatrix",
    "BacktestResult",
    "SystemConfig",
    "create_meta_portfolio_from_backtest",
    # Luck vs Skill (Lopez de Prado)
    "LuckQuantifier",
    "TrackRecordAnalyzer",
    "SkillAssessment",
    # SOPS Sizing (Sigmoidal + Giller + TapeSpeed)
    "SOPS",
    "TapeSpeed",
    "GillerScaler",
    "SOPSGillerSizer",
    "AdaptiveKEstimator",
    "SOPSState",
    "TapeSpeedState",
    "create_sops_sizer",
]
