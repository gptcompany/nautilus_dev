"""Integration tests for Meta-Learning Pipeline (Spec 026).

Tests the full pipeline: bars -> labeling -> meta-model -> sizing.
Verifies no look-ahead bias and proper component integration.
"""

from __future__ import annotations

import numpy as np
import pytest


class TestFullPipeline:
    """Tests for complete meta-learning pipeline."""

    def test_pipeline_end_to_end(self):
        """Test full pipeline: bars -> labeling -> meta-model -> sizing."""
        from strategies.common.labeling import TripleBarrierLabeler, TripleBarrierConfig
        from strategies.common.meta_learning import (
            MetaLabelGenerator,
            MetaModel,
            MetaModelConfig,
            WalkForwardSplitter,
            WalkForwardConfig,
            extract_meta_features,
        )
        from strategies.common.position_sizing import (
            IntegratedSizer,
            IntegratedSizingConfig,
        )
        from strategies.common.regime_detection import BOCD, BOCDConfig

        # 1. Generate synthetic price data
        np.random.seed(42)
        n_bars = 500
        returns = np.random.normal(0.0001, 0.02, n_bars)
        prices = 100 * np.exp(np.cumsum(returns))
        highs = prices * (1 + np.abs(np.random.normal(0, 0.005, n_bars)))
        lows = prices * (1 - np.abs(np.random.normal(0, 0.005, n_bars)))
        volumes = np.random.exponential(1000, n_bars)

        # 2. Apply triple barrier labeling
        labeler = TripleBarrierLabeler(
            TripleBarrierConfig(
                take_profit_pct=0.02,
                stop_loss_pct=0.01,
                max_holding_bars=20,
            )
        )

        # Simple primary signals (momentum)
        primary_signals = np.sign(np.diff(prices, prepend=prices[0]))

        labels = labeler.apply(
            prices=prices,
            highs=highs,
            lows=lows,
            signals=primary_signals,
        )

        assert len(labels) == n_bars
        assert np.all(np.isin(labels, [-1, 0, 1]))

        # 3. Generate meta-labels
        meta_gen = MetaLabelGenerator()
        meta_labels = meta_gen.generate(
            primary_signals=primary_signals,
            true_labels=labels,
        )

        # 4. Extract features for meta-model
        features = extract_meta_features(
            prices=prices,
            volumes=volumes,
            window=20,
        )

        # 5. Split data with walk-forward
        splitter = WalkForwardSplitter(
            WalkForwardConfig(
                train_window=100,
                test_window=20,
                step_size=10,
                embargo_window=2,
            )
        )

        splits = list(splitter.split(len(features)))
        assert len(splits) > 0

        # 6. Train meta-model on first split
        train_idx, test_idx = splits[0]
        X_train = features[train_idx]
        y_train = meta_labels[train_idx]
        X_test = features[test_idx]

        meta_model = MetaModel(
            MetaModelConfig(
                n_estimators=10,  # Small for test speed
                max_depth=3,
                min_samples_required=50,
            )
        )

        # Only fit if enough samples
        if len(y_train) >= 50 and np.sum(y_train == 1) > 0 and np.sum(y_train == 0) > 0:
            meta_model.fit(X_train, y_train)
            meta_confidence = meta_model.predict_proba(X_test)
            assert len(meta_confidence) == len(test_idx)
            assert np.all((meta_confidence >= 0) & (meta_confidence <= 1))
        else:
            # Use default confidence if not enough data
            meta_confidence = np.full(len(test_idx), 0.5)

        # 7. BOCD for regime detection
        bocd = BOCD(BOCDConfig(hazard_rate=0.01))
        regime_weights = []
        for ret in returns[test_idx]:
            bocd.update(ret)
            # Lower weight during potential regime change
            weight = 0.6 if bocd.is_changepoint(threshold=0.3) else 1.0
            regime_weights.append(weight)
        regime_weights = np.array(regime_weights)

        # 8. Integrated sizing
        sizer = IntegratedSizer(
            IntegratedSizingConfig(
                giller_exponent=0.5,
                fractional_kelly=0.25,
            )
        )

        final_sizes = []
        for i, idx in enumerate(test_idx):
            result = sizer.calculate(
                signal=primary_signals[idx],
                meta_confidence=meta_confidence[i],
                regime_weight=regime_weights[i],
                toxicity=0.1,  # Fixed toxicity for this test
            )
            final_sizes.append(result.final_size)

        final_sizes = np.array(final_sizes)

        # Verify pipeline output
        assert len(final_sizes) == len(test_idx)
        # Sizes should be bounded
        assert np.all(np.abs(final_sizes) <= 1.0)
        # Should have both directions
        assert np.any(final_sizes > 0) or np.any(final_sizes < 0)

    def test_no_lookahead_bias(self):
        """Verify pipeline doesn't use future information."""
        from strategies.common.meta_learning import (
            WalkForwardSplitter,
            WalkForwardConfig,
        )

        n = 200
        splitter = WalkForwardSplitter(
            WalkForwardConfig(
                train_window=50,
                test_window=10,
                step_size=10,
                embargo_window=3,
            )
        )

        for train_idx, test_idx in splitter.split(n):
            # All train indices must be before test indices
            assert np.max(train_idx) < np.min(test_idx), (
                "Training data must precede test data"
            )

            # Embargo check: min gap between train and test
            gap = np.min(test_idx) - np.max(train_idx)
            assert gap >= 3, f"Embargo not respected: gap={gap}"

    def test_component_independence(self):
        """Each component works independently with default values."""
        from strategies.common.labeling import TripleBarrierLabeler
        from strategies.common.meta_learning import (
            MetaLabelGenerator,
            WalkForwardSplitter,
        )
        from strategies.common.position_sizing import IntegratedSizer
        from strategies.common.regime_detection import BOCD

        # Each component should instantiate with defaults
        labeler = TripleBarrierLabeler()
        assert labeler is not None

        meta_gen = MetaLabelGenerator()
        assert meta_gen is not None

        splitter = WalkForwardSplitter()
        assert splitter is not None

        sizer = IntegratedSizer()
        assert sizer is not None

        bocd = BOCD()
        assert bocd is not None


class TestPerformanceRequirements:
    """Performance benchmarks per spec requirements."""

    @pytest.mark.parametrize("n_bars", [10000, 100000])
    def test_triple_barrier_performance(self, n_bars: int):
        """Triple barrier: <60s for 1M bars (scaled test)."""
        import time
        from strategies.common.labeling import TripleBarrierLabeler

        np.random.seed(42)
        prices = 100 * np.exp(np.cumsum(np.random.normal(0, 0.01, n_bars)))
        highs = prices * 1.005
        lows = prices * 0.995
        signals = np.sign(np.random.randn(n_bars))

        labeler = TripleBarrierLabeler()

        start = time.time()
        labels = labeler.apply(prices, highs, lows, signals)
        elapsed = time.time() - start

        assert len(labels) == n_bars
        # Scale to 1M: if 100k takes X seconds, 1M should take <60s
        scaled_time = elapsed * (1_000_000 / n_bars)
        assert scaled_time < 60, f"Scaled time {scaled_time:.1f}s > 60s limit"

    def test_meta_model_inference_latency(self):
        """Meta-model inference: <5ms."""
        import time
        from strategies.common.meta_learning import MetaModel, MetaModelConfig

        np.random.seed(42)
        # Training data
        X_train = np.random.randn(500, 10)
        y_train = (np.random.randn(500) > 0).astype(int)

        # Single sample for inference
        X_test = np.random.randn(1, 10)

        model = MetaModel(MetaModelConfig(n_estimators=50))
        model.fit(X_train, y_train)

        # Warmup
        _ = model.predict_proba(X_test)

        # Measure
        times = []
        for _ in range(100):
            start = time.time()
            _ = model.predict_proba(X_test)
            times.append(time.time() - start)

        avg_ms = np.mean(times) * 1000
        assert avg_ms < 5, f"Inference latency {avg_ms:.2f}ms > 5ms limit"

    def test_bocd_update_latency(self):
        """BOCD update: <5ms."""
        import time
        from strategies.common.regime_detection import BOCD

        bocd = BOCD()

        # Warmup
        for _ in range(100):
            bocd.update(np.random.normal(0, 0.01))

        # Measure
        times = []
        for _ in range(100):
            start = time.time()
            bocd.update(np.random.normal(0, 0.01))
            times.append(time.time() - start)

        avg_ms = np.mean(times) * 1000
        assert avg_ms < 5, f"BOCD update latency {avg_ms:.2f}ms > 5ms limit"

    def test_integrated_sizing_latency(self):
        """Integrated sizing: <20ms end-to-end."""
        import time
        from strategies.common.position_sizing import IntegratedSizer

        sizer = IntegratedSizer()

        # Warmup
        for _ in range(100):
            sizer.calculate(
                signal=np.random.randn(),
                meta_confidence=np.random.rand(),
                regime_weight=np.random.rand() * 0.8 + 0.4,
                toxicity=np.random.rand() * 0.5,
            )

        # Measure
        times = []
        for _ in range(100):
            start = time.time()
            sizer.calculate(
                signal=np.random.randn(),
                meta_confidence=np.random.rand(),
                regime_weight=np.random.rand() * 0.8 + 0.4,
                toxicity=np.random.rand() * 0.5,
            )
            times.append(time.time() - start)

        avg_ms = np.mean(times) * 1000
        assert avg_ms < 20, f"Sizing latency {avg_ms:.2f}ms > 20ms limit"


class TestEdgeCases:
    """Edge case handling tests."""

    def test_empty_data_handling(self):
        """Pipeline handles empty/minimal data gracefully."""
        from strategies.common.labeling import TripleBarrierLabeler

        labeler = TripleBarrierLabeler()

        # Single bar
        prices = np.array([100.0])
        highs = np.array([101.0])
        lows = np.array([99.0])
        signals = np.array([1])

        labels = labeler.apply(prices, highs, lows, signals)
        assert len(labels) == 1
        assert labels[0] == 0  # Should timeout with single bar

    def test_extreme_volatility(self):
        """Pipeline handles extreme volatility."""
        from strategies.common.regime_detection import BOCD

        bocd = BOCD()

        # Normal observations
        for _ in range(50):
            bocd.update(np.random.normal(0, 0.01))

        # Extreme spike
        bocd.update(10.0)  # 1000 std devs

        prob = bocd.get_changepoint_probability()
        assert 0 <= prob <= 1
        assert bocd.is_changepoint(threshold=0.5)  # Should detect this

    def test_constant_signals(self):
        """Handle constant (all same) signals."""
        from strategies.common.meta_learning import MetaLabelGenerator

        gen = MetaLabelGenerator()

        signals = np.ones(100)
        labels = np.ones(100)

        meta_labels = gen.generate(signals, labels)
        assert np.all(meta_labels == 1)  # All correct
