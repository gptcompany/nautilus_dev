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

from .adaptive_decay import (
    AdaptiveDecayCalculator,
    VolatilityContext,
)
from .alpha_evolve_bridge import (
    AdaptiveSurvivalSystem,
    AlphaEvolveBridge,
    EvolutionConfig,
    EvolutionRequest,
    EvolutionTrigger,
)
from .correlation_tracker import (
    CorrelationMetrics,
    OnlineCorrelationMatrix,
    OnlineStats,
    calculate_covariance_penalty,
)
from .dsp_filters import (
    DSPRegimeDetector,
    IIRHighPass,
    IIRLowPass,
    IIRRegimeDetector,
    KalmanFilter1D,
    LMSAdaptiveFilter,
    RecursiveVariance,
)
from .ensemble_selection import (
    EnsembleResult,
    EnsembleSelector,
    SelectedStrategy,
    calculate_returns_correlation,
    select_ensemble,
)
from .flow_physics import (
    FlowState,
    InformationDiffusion,
    MarketFlowAnalyzer,
    WaveEquationAnalyzer,
)
from .information_theory import (
    EntropyEstimator,
    InformationBasedRiskManager,
    InformationState,
    MutualInformationEstimator,
    OptimalSamplingAnalyzer,
    WienerFilter,
)
from .luck_skill import (
    LuckQuantifier,
    OverfitAlert,
    OverfittingDetector,
    SkillAssessment,
    TrackRecordAnalyzer,
    probabilistic_sharpe_ratio,
)
from .meta_controller import MarketHarmony, MetaController, MetaState, SystemState
from .meta_portfolio import (
    BacktestMatrix,
    BacktestResult,
    MetaPortfolio,
    SystemConfig,
    create_meta_portfolio_from_backtest,
)
from .multi_dimensional_regime import (
    ConsensusRegime,
    DimensionResult,
    MultiDimensionalRegimeDetector,
    MultiDimensionalResult,
    create_multi_regime_detector,
)
from .particle_portfolio import (
    BayesianEnsemble,
    Particle,
    ParticlePortfolio,
    PortfolioState,
    ThompsonSelector,
)
from .pid_drawdown import PIDDrawdownController, SimpleDrawdownScaler
from .regime_integration import (
    CombinedRegime,
    EnhancedRegimeManager,
    EnhancedRegimeResult,
)
from .sops_sizing import (
    SOPS,
    AdaptiveKEstimator,
    GillerScaler,
    SOPSGillerSizer,
    SOPSState,
    TapeSpeed,
    TapeSpeedState,
    create_sops_sizer,
)
from .spectral_regime import MarketRegime, SpectralRegimeDetector
from .system_health import HealthState, SystemHealthMonitor
from .transaction_costs import (
    BacktestCostAdjuster,
    CostProfile,
    Exchange,
    TransactionCost,
    TransactionCostModel,
    get_recommended_profile,
)

# NOTE: universal_laws removed (2026-01-05) - PMW validation found no academic evidence
# for Fibonacci/wave physics in trading. See CLAUDE.md for details.
from .vibration_analysis import (
    DigitalRootAnalyzer,
    HarmonicRatioAnalyzer,
    ResonanceEvent,
    VibrationAnalyzer,
    VibrationMode,
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
    # MVP: Probabilistic Sharpe & Overfitting Detection (ROI 10.0 / 7.5)
    "probabilistic_sharpe_ratio",
    "OverfittingDetector",
    "OverfitAlert",
    # MVP: Ensemble Selection (ROI 7.5)
    "select_ensemble",
    "EnsembleSelector",
    "EnsembleResult",
    "SelectedStrategy",
    "calculate_returns_correlation",
    # MVP: Transaction Cost Modeling (ROI 5.0)
    "TransactionCostModel",
    "TransactionCost",
    "BacktestCostAdjuster",
    "CostProfile",
    "Exchange",
    "get_recommended_profile",
    # SOPS Sizing (Sigmoidal + Giller + TapeSpeed)
    "SOPS",
    "TapeSpeed",
    "GillerScaler",
    "SOPSGillerSizer",
    "AdaptiveKEstimator",
    "SOPSState",
    "TapeSpeedState",
    "create_sops_sizer",
    # Adaptive Decay (Spec 032)
    "VolatilityContext",
    "AdaptiveDecayCalculator",
]
