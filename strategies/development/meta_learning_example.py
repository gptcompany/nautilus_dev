"""Meta-Learning Example Strategy (Spec 026).

Demonstrates the full meta-learning pipeline integration:
- Triple Barrier Labeling
- Meta-Model for confidence estimation
- BOCD for regime detection
- Integrated position sizing

This example shows warmup patterns and factor contribution logging.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import TYPE_CHECKING

import numpy as np
from nautilus_trader.config import StrategyConfig
from nautilus_trader.indicators.atr import AverageTrueRange
from nautilus_trader.indicators.average.ema import ExponentialMovingAverage
from nautilus_trader.model.identifiers import InstrumentId
from nautilus_trader.trading.strategy import Strategy

from strategies.common.labeling import TripleBarrierConfig, TripleBarrierLabeler
from strategies.common.meta_learning import (
    MetaLabelGenerator,
    MetaModel,
    MetaModelConfig,
    WalkForwardConfig,
    WalkForwardSplitter,
    extract_meta_features,
)
from strategies.common.position_sizing import IntegratedSizer, IntegratedSizingConfig
from strategies.common.regime_detection import BOCD, BOCDConfig

if TYPE_CHECKING:
    from nautilus_trader.model.data import Bar

logger = logging.getLogger(__name__)


class MetaLearningExampleConfig(StrategyConfig):
    """Configuration for MetaLearningExampleStrategy."""

    instrument_id: str
    bar_type: str

    # Indicator periods
    ema_fast: int = 10
    ema_slow: int = 30
    atr_period: int = 14

    # Triple barrier settings
    take_profit_atr: float = 2.0
    stop_loss_atr: float = 1.0
    max_holding_bars: int = 20

    # Meta-model settings
    warmup_bars: int = 252
    retrain_frequency: int = 21

    # Position sizing
    fractional_kelly: float = 0.25
    max_position_size: float = 0.1


class MetaLearningExampleStrategy(Strategy):
    """Example strategy demonstrating meta-learning pipeline.

    This strategy combines:
    1. Simple momentum signal (EMA crossover)
    2. Triple barrier labeling for training data
    3. Meta-model for confidence estimation
    4. BOCD for regime change detection
    5. Integrated position sizing

    Attributes:
        config: Strategy configuration.
        instrument: Trading instrument.
        bar_type: Bar type for data.
    """

    def __init__(self, config: MetaLearningExampleConfig) -> None:
        """Initialize the strategy."""
        super().__init__(config)

        # Configuration
        self._instrument_id = InstrumentId.from_str(config.instrument_id)
        self._bar_type = None  # Set in on_start

        # Native Rust indicators
        self._ema_fast = ExponentialMovingAverage(config.ema_fast)
        self._ema_slow = ExponentialMovingAverage(config.ema_slow)
        self._atr = AverageTrueRange(config.atr_period)

        # Historical data buffers
        self._prices: list[float] = []
        self._highs: list[float] = []
        self._lows: list[float] = []
        self._volumes: list[float] = []
        self._signals: list[int] = []
        self._returns: list[float] = []

        # Meta-learning components
        self._labeler = TripleBarrierLabeler(
            TripleBarrierConfig(
                take_profit_pct=config.take_profit_atr * 0.01,  # Convert ATR multiple
                stop_loss_pct=config.stop_loss_atr * 0.01,
                max_holding_bars=config.max_holding_bars,
            )
        )

        self._meta_gen = MetaLabelGenerator()

        self._meta_model = MetaModel(
            MetaModelConfig(
                n_estimators=100,
                max_depth=5,
                min_samples_required=100,
            )
        )

        self._splitter = WalkForwardSplitter(
            WalkForwardConfig(
                train_window=252,
                test_window=63,
                step_size=21,
                embargo_size=5,
            )
        )

        self._bocd = BOCD(BOCDConfig(hazard_rate=0.01, detection_threshold=0.5))

        self._sizer = IntegratedSizer(
            IntegratedSizingConfig(
                giller_exponent=0.5,
                fractional_kelly=config.fractional_kelly,
                max_size=config.max_position_size,
            )
        )

        # State tracking
        self._is_warmed_up = False
        self._bars_since_retrain = 0
        self._last_regime_weight = 1.0

    def on_start(self) -> None:
        """Handle strategy startup."""
        from nautilus_trader.model.data import BarType

        self._bar_type = BarType.from_str(self.config.bar_type)

        # Subscribe to bars
        self.subscribe_bars(self._bar_type)

        # Request historical data for warmup
        self.request_bars(
            bar_type=self._bar_type,
            start=self.clock.utc_now() - timedelta(days=365),
            callback=self._on_warmup_complete,
        )

        logger.info("MetaLearningExampleStrategy started, requesting warmup data...")

    def _on_warmup_complete(self, bars: list) -> None:
        """Handle warmup data completion."""
        if not bars:
            logger.warning("No warmup bars received")
            return

        for bar in bars:
            self._process_bar_for_warmup(bar)

        if len(self._prices) >= self.config.warmup_bars:
            self._train_meta_model()
            self._is_warmed_up = True
            logger.info(
                "Warmup complete: %d bars processed, meta-model trained",
                len(self._prices),
            )

    def _process_bar_for_warmup(self, bar: Bar) -> None:
        """Process a single bar during warmup."""
        # Update indicators
        self._ema_fast.handle_bar(bar)
        self._ema_slow.handle_bar(bar)
        self._atr.handle_bar(bar)

        # Store data
        close = float(bar.close)
        self._prices.append(close)
        self._highs.append(float(bar.high))
        self._lows.append(float(bar.low))
        self._volumes.append(float(bar.volume))

        # Calculate return
        if len(self._prices) > 1:
            ret = (self._prices[-1] - self._prices[-2]) / self._prices[-2]
            self._returns.append(ret)
        else:
            self._returns.append(0.0)

        # Generate signal
        if self._ema_fast.initialized and self._ema_slow.initialized:
            signal = 1 if self._ema_fast.value > self._ema_slow.value else -1
        else:
            signal = 0
        self._signals.append(signal)

    def _train_meta_model(self) -> None:
        """Train the meta-model on historical data."""
        prices = np.array(self._prices)
        highs = np.array(self._highs)
        lows = np.array(self._lows)
        volumes = np.array(self._volumes)
        signals = np.array(self._signals)

        # Generate labels using triple barrier
        labels = self._labeler.apply(prices, highs, lows, signals)

        # Generate meta-labels
        meta_labels = self._meta_gen.generate(signals, labels)

        # Extract features
        features = extract_meta_features(prices, volumes, window=20)

        # Get latest training window
        splits = list(self._splitter.split(len(features)))
        if not splits:
            logger.warning("No valid walk-forward splits")
            return

        train_idx, _ = splits[-1]

        X_train = features[train_idx]
        y_train = meta_labels[train_idx]

        # Train if enough samples
        if len(y_train) >= 100 and np.sum(y_train == 1) >= 10 and np.sum(y_train == 0) >= 10:
            self._meta_model.fit(X_train, y_train)
            logger.info(
                "Meta-model trained on %d samples (accuracy: %.2f)",
                len(y_train),
                np.mean(y_train),
            )
        else:
            logger.warning(
                "Insufficient training data: %d samples, skipping retrain",
                len(y_train),
            )

    def on_bar(self, bar: Bar) -> None:
        """Handle new bar data."""
        # Always process bar for data collection
        self._process_bar_for_warmup(bar)

        # Update BOCD with latest return
        if len(self._returns) > 0:
            self._bocd.update(self._returns[-1])

            # Adjust regime weight based on changepoint detection
            if self._bocd.is_changepoint():
                self._last_regime_weight = 0.6  # Reduce exposure during regime change
                logger.info(
                    "Regime change detected! P(changepoint)=%.3f",
                    self._bocd.get_changepoint_probability(),
                )
            else:
                # Gradually restore weight
                self._last_regime_weight = min(1.0, self._last_regime_weight + 0.02)

        # Check for retrain
        self._bars_since_retrain += 1
        if self._bars_since_retrain >= self.config.retrain_frequency:
            self._train_meta_model()
            self._bars_since_retrain = 0

        # Skip trading if not warmed up
        if not self._is_warmed_up:
            return

        # Generate trading signal
        signal = self._signals[-1] if self._signals else 0
        if signal == 0:
            return

        # Get meta-model confidence
        if len(self._prices) >= 20 and len(self._volumes) >= 20:
            features = extract_meta_features(
                np.array(self._prices[-100:]),
                np.array(self._volumes[-100:]),
                window=20,
            )
            if len(features) > 0:
                meta_confidence = self._meta_model.predict_proba(features[-1:])
                meta_conf = float(meta_confidence[0])
            else:
                meta_conf = 0.5
        else:
            meta_conf = 0.5

        # Calculate position size using integrated sizer
        result = self._sizer.calculate(
            signal=float(signal),
            meta_confidence=meta_conf,
            regime_weight=self._last_regime_weight,
            toxicity=0.1,  # Would come from VPIN in production
        )

        # Log factor contributions (FR-008)
        logger.debug(
            "Position sizing factors: signal=%.2f, meta=%.3f, regime=%.3f, "
            "toxicity=%.3f -> size=%.4f",
            result.factors.get("signal", 0),
            result.factors.get("meta_confidence", 0),
            result.factors.get("regime_weight", 0),
            result.factors.get("toxicity_penalty", 0),
            result.final_size,
        )

        # In production, would submit orders here
        if abs(result.final_size) > 0.001:
            logger.info(
                "Trade signal: direction=%d, size=%.4f (meta=%.2f, regime=%.2f)",
                result.direction,
                result.final_size,
                meta_conf,
                self._last_regime_weight,
            )

    def on_stop(self) -> None:
        """Handle strategy shutdown."""
        logger.info(
            "MetaLearningExampleStrategy stopped. Processed %d bars, meta-model trained.",
            len(self._prices),
        )

        # Log final feature importance if available
        importance = self._meta_model.feature_importance
        if importance is not None and len(importance) > 0:
            top_features = np.argsort(importance)[-5:][::-1]
            logger.info("Top 5 feature importances: %s", importance[top_features])
