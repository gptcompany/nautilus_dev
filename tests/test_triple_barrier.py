"""Tests for Triple Barrier Labeling (Spec 026 - US1).

TDD RED Phase: These tests should FAIL until implementation is complete.
"""

from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.meta_learning
class TestTripleBarrierLabeler:
    """Test suite for TripleBarrierLabeler class."""

    def test_apply_returns_labels_for_all_bars(
        self, sample_price_series, sample_atr_values, triple_barrier_config
    ):
        """Test that apply() returns labels for valid entry points."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        labeler = TripleBarrierLabeler(triple_barrier_config)
        labels = labeler.apply(sample_price_series, sample_atr_values)

        # Should return labels (allow for edge cases at end)
        assert len(labels) == len(sample_price_series)
        # All labels should be -1, 0, or +1
        assert np.all(np.isin(labels, [-1, 0, 1]))

    def test_take_profit_label_when_tp_hit_first(self, triple_barrier_config):
        """Test +1 label when take-profit barrier is hit first."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        # Price rises to hit TP before SL or timeout
        # Entry at 100, ATR = 1, TP = 100 + 2*1 = 102, SL = 100 - 1*1 = 99
        prices = np.array([100.0, 100.5, 101.0, 102.5, 102.0], dtype=np.float64)
        atr = np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float64)

        labeler = TripleBarrierLabeler(triple_barrier_config)
        labels = labeler.apply(prices, atr)

        # First entry should be +1 (take profit hit at index 3)
        assert labels[0] == 1

    def test_stop_loss_label_when_sl_hit_first(self, triple_barrier_config):
        """Test -1 label when stop-loss barrier is hit first."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        # Price drops to hit SL before TP or timeout
        # Entry at 100, ATR = 1, TP = 102, SL = 99
        prices = np.array([100.0, 99.5, 98.5, 99.0, 100.0], dtype=np.float64)
        atr = np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float64)

        labeler = TripleBarrierLabeler(triple_barrier_config)
        labels = labeler.apply(prices, atr)

        # First entry should be -1 (stop loss hit at index 2)
        assert labels[0] == -1

    def test_timeout_label_when_no_barrier_hit(self):
        """Test label on timeout when neither barrier is hit.

        Per spec: "Given max holding period reached, When labeled, Then returns
        0 or sign of return". Returns sign of final return, not always 0.
        """
        from strategies.common.labeling.config import TripleBarrierConfig
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        config = TripleBarrierConfig(
            pt_multiplier=2.0,
            sl_multiplier=1.0,
            max_holding_bars=3,  # Short timeout
        )

        # Price stays within barriers until timeout, but ends exactly at entry
        # Entry at 100, ATR = 1, TP = 102, SL = 99
        # Price at timeout (bar 3) = 100.0, same as entry -> return = 0
        prices = np.array([100.0, 100.2, 100.1, 100.0, 100.0], dtype=np.float64)
        atr = np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float64)

        labeler = TripleBarrierLabeler(config)
        labels = labeler.apply(prices, atr)

        # First entry should be 0 (timeout with zero return)
        assert labels[0] == 0

    def test_atr_based_barrier_calculation(self, triple_barrier_config):
        """Test that barriers are calculated using ATR values."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        # With higher ATR, barriers should be wider
        prices = np.array([100.0, 103.0, 104.0, 105.0, 106.0], dtype=np.float64)
        atr_small = np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float64)
        atr_large = np.array([5.0, 5.0, 5.0, 5.0, 5.0], dtype=np.float64)

        labeler = TripleBarrierLabeler(triple_barrier_config)

        # With small ATR (TP=102, SL=99), price 103 should trigger TP
        labels_small = labeler.apply(prices, atr_small)
        assert labels_small[0] == 1  # TP hit

        # With large ATR (TP=110, SL=95), price 106 should NOT trigger TP
        labels_large = labeler.apply(prices, atr_large)
        # Timeout with positive return (106 - 100 = +6) -> label = +1
        # This tests that wider ATR barriers prevent premature TP/SL triggers
        assert labels_large[0] == 1  # Positive return at timeout

    def test_vectorized_batch_processing(
        self, sample_price_series, sample_atr_values, triple_barrier_config
    ):
        """Test that labeler processes batches efficiently (vectorized)."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        labeler = TripleBarrierLabeler(triple_barrier_config)

        # Should process 500 bars quickly
        import time

        start = time.time()
        labels = labeler.apply(sample_price_series, sample_atr_values)
        elapsed = time.time() - start

        # Should complete in under 1 second for 500 bars
        assert elapsed < 1.0
        assert len(labels) == len(sample_price_series)

    def test_signals_filter_entry_points(
        self,
        sample_price_series,
        sample_atr_values,
        sample_signals,
        triple_barrier_config,
    ):
        """Test that signals parameter filters which bars get labeled."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        labeler = TripleBarrierLabeler(triple_barrier_config)

        # Create signals with only some entries
        signals = np.zeros(len(sample_price_series), dtype=np.int64)
        signals[10] = 1  # Long at index 10
        signals[50] = -1  # Short at index 50

        labels = labeler.apply(sample_price_series, sample_atr_values, signals=signals)

        # Only entries with non-zero signals should have labels
        # (other entries should remain 0 as no trade was taken)
        np.where(signals != 0)[0]
        non_signal_indices = np.where(signals == 0)[0]

        # Non-signal entries should be 0 (no label)
        assert np.all(labels[non_signal_indices] == 0)


@pytest.mark.meta_learning
class TestBarrierEvents:
    """Test suite for detailed barrier event tracking."""

    def test_get_barrier_events_returns_details(
        self, sample_price_series, sample_atr_values, triple_barrier_config
    ):
        """Test that get_barrier_events returns BarrierEvent objects."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        labeler = TripleBarrierLabeler(triple_barrier_config)
        events = labeler.get_barrier_events(sample_price_series, sample_atr_values)

        # Should return list of BarrierEvent objects
        assert isinstance(events, list)
        if len(events) > 0:
            event = events[0]
            assert hasattr(event, "entry_idx")
            assert hasattr(event, "entry_price")
            assert hasattr(event, "tp_barrier")
            assert hasattr(event, "sl_barrier")
            assert hasattr(event, "exit_idx")
            assert hasattr(event, "label")

    def test_barrier_event_has_correct_prices(self, triple_barrier_config):
        """Test that barrier events have correct TP/SL prices."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        prices = np.array([100.0, 101.0, 102.5, 103.0], dtype=np.float64)
        atr = np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float64)

        labeler = TripleBarrierLabeler(triple_barrier_config)
        events = labeler.get_barrier_events(prices, atr)

        if len(events) > 0:
            event = events[0]
            # Entry at 100, ATR=1, pt_mult=2, sl_mult=1
            assert event.entry_price == 100.0
            assert event.tp_barrier == pytest.approx(102.0, rel=1e-5)  # 100 + 2*1
            assert event.sl_barrier == pytest.approx(99.0, rel=1e-5)  # 100 - 1*1


@pytest.mark.meta_learning
class TestBarrierHelpers:
    """Test suite for barrier calculation helper functions."""

    def test_get_vertical_barriers(self, triple_barrier_config):
        """Test vertical barrier (timeout) calculation."""
        from strategies.common.labeling.label_utils import get_vertical_barriers

        n = 100
        max_holding = triple_barrier_config.max_holding_bars

        barriers = get_vertical_barriers(n, max_holding)

        # Each barrier should be entry_idx + max_holding_bars
        for i in range(n - max_holding):
            assert barriers[i] == i + max_holding

        # Last entries should have barriers capped at n-1
        for i in range(n - max_holding, n):
            assert barriers[i] <= n - 1

    def test_get_horizontal_barriers(self, triple_barrier_config):
        """Test horizontal barrier (TP/SL) calculation."""
        from strategies.common.labeling.label_utils import get_horizontal_barriers

        prices = np.array([100.0, 105.0, 95.0, 110.0], dtype=np.float64)
        atr = np.array([2.0, 2.5, 1.5, 3.0], dtype=np.float64)

        tp_barriers, sl_barriers = get_horizontal_barriers(
            prices,
            atr,
            pt_multiplier=triple_barrier_config.pt_multiplier,
            sl_multiplier=triple_barrier_config.sl_multiplier,
        )

        # TP = price + pt_mult * ATR
        expected_tp = prices + triple_barrier_config.pt_multiplier * atr
        np.testing.assert_array_almost_equal(tp_barriers, expected_tp)

        # SL = price - sl_mult * ATR
        expected_sl = prices - triple_barrier_config.sl_multiplier * atr
        np.testing.assert_array_almost_equal(sl_barriers, expected_sl)


@pytest.mark.meta_learning
class TestEdgeCases:
    """Test edge cases for triple barrier labeling."""

    def test_short_price_series(self, triple_barrier_config):
        """Test handling of price series shorter than max_holding_bars."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        # Series shorter than max_holding_bars
        prices = np.array([100.0, 101.0, 102.0], dtype=np.float64)
        atr = np.array([1.0, 1.0, 1.0], dtype=np.float64)

        labeler = TripleBarrierLabeler(triple_barrier_config)
        labels = labeler.apply(prices, atr)

        # Should handle gracefully
        assert len(labels) == len(prices)

    def test_empty_price_series(self, triple_barrier_config):
        """Test handling of empty price series."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        prices = np.array([], dtype=np.float64)
        atr = np.array([], dtype=np.float64)

        labeler = TripleBarrierLabeler(triple_barrier_config)
        labels = labeler.apply(prices, atr)

        assert len(labels) == 0

    def test_mismatched_array_lengths(self, triple_barrier_config):
        """Test that mismatched array lengths raise error."""
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        prices = np.array([100.0, 101.0, 102.0], dtype=np.float64)
        atr = np.array([1.0, 1.0], dtype=np.float64)  # Wrong length

        labeler = TripleBarrierLabeler(triple_barrier_config)

        with pytest.raises(ValueError):
            labeler.apply(prices, atr)

    def test_no_barrier_hit_returns_final_return_sign(self):
        """Test that timeout label uses sign of final return (edge case FR from spec)."""
        from strategies.common.labeling.config import TripleBarrierConfig
        from strategies.common.labeling.triple_barrier import TripleBarrierLabeler

        config = TripleBarrierConfig(
            pt_multiplier=10.0,  # Very wide barriers
            sl_multiplier=10.0,
            max_holding_bars=3,
        )

        # Price goes up slightly (positive return at timeout)
        prices_up = np.array([100.0, 100.5, 101.0, 101.5, 102.0], dtype=np.float64)
        atr = np.array([1.0, 1.0, 1.0, 1.0, 1.0], dtype=np.float64)

        labeler = TripleBarrierLabeler(config)
        labels_up = labeler.apply(prices_up, atr)

        # Should use sign of return when timeout without barrier hit
        # Return is positive, so label should be 0 or +1 depending on min_return
        assert labels_up[0] in [0, 1]

        # Price goes down slightly (negative return at timeout)
        prices_down = np.array([100.0, 99.5, 99.0, 98.5, 98.0], dtype=np.float64)
        labels_down = labeler.apply(prices_down, atr)

        # Negative return, but barriers not hit
        assert labels_down[0] in [0, -1]


@pytest.mark.meta_learning
class TestModuleImports:
    """Test that module __init__.py exports work correctly."""

    def test_import_from_labeling_module(self):
        """Test imports from strategies.common.labeling."""
        from strategies.common.labeling import (
            TripleBarrierConfig,
            TripleBarrierLabeler,
            get_horizontal_barriers,
            get_vertical_barriers,
        )

        # Verify we got the right classes
        assert TripleBarrierLabeler is not None
        assert TripleBarrierConfig is not None
        assert get_vertical_barriers is not None
        assert get_horizontal_barriers is not None

    def test_import_from_meta_learning_module(self):
        """Test imports from strategies.common.meta_learning."""
        from strategies.common.meta_learning import (
            MetaLabelGenerator,
            MetaModel,
            MetaModelConfig,
            WalkForwardConfig,
            WalkForwardSplitter,
            extract_meta_features,
        )

        # Verify we got the right classes
        assert MetaModel is not None
        assert MetaModelConfig is not None
        assert MetaLabelGenerator is not None
        assert WalkForwardSplitter is not None
        assert WalkForwardConfig is not None
        assert extract_meta_features is not None
