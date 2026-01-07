"""Tests for Walk-Forward Validation (Spec 026 - US2).

TDD RED Phase: These tests should FAIL until implementation is complete.
"""

from __future__ import annotations

import numpy as np
import pytest


@pytest.mark.meta_learning
class TestWalkForwardSplitter:
    """Test suite for WalkForwardSplitter class."""

    def test_generates_correct_number_of_splits(self, walk_forward_config):
        """Test that splitter generates expected number of splits."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        splits = splitter.split(n_samples)

        # Calculate expected number of splits
        # Each split needs: train_window + embargo + test_window
        total_per_split = (
            walk_forward_config.train_window
            + walk_forward_config.embargo_size
            + walk_forward_config.test_window
        )
        expected_splits = (n_samples - total_per_split) // walk_forward_config.step_size + 1

        assert len(splits) >= expected_splits - 1
        assert len(splits) > 0

    def test_train_test_separation(self, walk_forward_config):
        """Test that train and test indices don't overlap."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        splits = splitter.split(n_samples)

        for train_idx, test_idx in splits:
            train_set = set(train_idx)
            test_set = set(test_idx)

            # No overlap between train and test
            assert len(train_set & test_set) == 0

            # Train comes before test
            assert max(train_idx) < min(test_idx)

    def test_embargo_respected(self, walk_forward_config):
        """Test that embargo gap exists between train and test."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        splits = splitter.split(n_samples)

        for train_idx, test_idx in splits:
            # Gap between train end and test start should be >= embargo
            gap = min(test_idx) - max(train_idx) - 1
            assert gap >= walk_forward_config.embargo_size

    def test_rolling_windows(self, walk_forward_config):
        """Test that windows roll forward correctly."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        splits = splitter.split(n_samples)

        if len(splits) < 2:
            pytest.skip("Not enough data for multiple splits")

        # Check that train windows roll forward
        for i in range(len(splits) - 1):
            train1_start = splits[i][0][0]
            train2_start = splits[i + 1][0][0]

            # Second train window should start step_size bars later
            assert train2_start == train1_start + walk_forward_config.step_size

    def test_correct_window_sizes(self, walk_forward_config):
        """Test that train and test windows have correct sizes."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        splits = splitter.split(n_samples)

        for train_idx, test_idx in splits:
            # Train window should be correct size
            assert len(train_idx) == walk_forward_config.train_window

            # Test window should be correct size (may be smaller at end)
            assert len(test_idx) <= walk_forward_config.test_window
            assert len(test_idx) > 0


@pytest.mark.meta_learning
class TestNoLookAhead:
    """Test suite for look-ahead bias prevention."""

    def test_no_future_data_in_training(self, walk_forward_config):
        """Test that training data never includes future test data."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        splits = splitter.split(n_samples)

        for train_idx, test_idx in splits:
            # All train indices should be before first test index
            assert max(train_idx) < min(test_idx)

    def test_chronological_ordering(self, walk_forward_config):
        """Test that all indices are chronologically ordered."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        splits = splitter.split(n_samples)

        for train_idx, test_idx in splits:
            # Indices should be sorted
            assert np.all(np.diff(train_idx) == 1)  # Consecutive
            assert np.all(np.diff(test_idx) == 1)  # Consecutive


@pytest.mark.meta_learning
class TestPurgingAndEmbargo:
    """Test suite for purging overlapping labels."""

    def test_purge_removes_overlapping_samples(self, walk_forward_config):
        """Test that purging removes samples with labels extending into test period."""
        from strategies.common.meta_learning.walk_forward import WalkForwardSplitter

        splitter = WalkForwardSplitter(walk_forward_config)

        n_samples = 500
        max_holding = 10  # Labels span up to 10 bars

        splits = splitter.split(n_samples)
        purged_splits = splitter.purge_splits(splits, max_holding_bars=max_holding)

        for (orig_train, _), (purged_train, purged_test) in zip(splits, purged_splits, strict=False):
            # Purged train should be smaller or equal
            assert len(purged_train) <= len(orig_train)

            # Last purged train index should be far enough from test
            if len(purged_train) > 0 and len(purged_test) > 0:
                gap = min(purged_test) - max(purged_train)
                # Gap should account for label span
                assert gap >= max_holding


@pytest.mark.meta_learning
class TestWalkForwardTrain:
    """Test suite for walk_forward_train utility function."""

    def test_walk_forward_train_basic(self, walk_forward_config):
        """Test basic walk-forward training loop."""
        from sklearn.ensemble import RandomForestClassifier

        from strategies.common.meta_learning.walk_forward import walk_forward_train

        # Create synthetic data
        n_samples = 400
        n_features = 5
        np.random.seed(42)
        features = np.random.randn(n_samples, n_features)
        meta_labels = np.random.randint(0, 2, n_samples)

        # Create a simple model
        model = RandomForestClassifier(n_estimators=10, random_state=42)

        # Run walk-forward training
        result = walk_forward_train(
            model=model,
            features=features,
            meta_labels=meta_labels,
            config=walk_forward_config,
        )

        # Check result structure
        assert "predictions" in result
        assert "actuals" in result
        assert "indices" in result
        assert "n_splits" in result

        # Check that predictions were made
        assert len(result["predictions"]) > 0
        assert len(result["actuals"]) == len(result["predictions"])
        assert len(result["indices"]) == len(result["predictions"])

    def test_walk_forward_train_with_purging(self, walk_forward_config):
        """Test walk-forward with purging for triple barrier labels."""
        from sklearn.ensemble import RandomForestClassifier

        from strategies.common.meta_learning.walk_forward import walk_forward_train

        n_samples = 400
        n_features = 5
        np.random.seed(42)
        features = np.random.randn(n_samples, n_features)
        meta_labels = np.random.randint(0, 2, n_samples)

        model = RandomForestClassifier(n_estimators=10, random_state=42)

        # Run with purging
        result = walk_forward_train(
            model=model,
            features=features,
            meta_labels=meta_labels,
            config=walk_forward_config,
            max_holding_bars=10,
        )

        assert result["n_splits"] > 0
        # With purging, may have fewer predictions per split
        assert len(result["predictions"]) > 0

    def test_walk_forward_train_predict_without_proba(self, walk_forward_config):
        """Test walk-forward with model that has no predict_proba."""
        from sklearn.svm import LinearSVC

        from strategies.common.meta_learning.walk_forward import walk_forward_train

        n_samples = 400
        n_features = 5
        np.random.seed(42)
        features = np.random.randn(n_samples, n_features)
        meta_labels = np.random.randint(0, 2, n_samples)

        # LinearSVC has no predict_proba by default
        model = LinearSVC(dual=True, random_state=42, max_iter=1000)

        result = walk_forward_train(
            model=model,
            features=features,
            meta_labels=meta_labels,
            config=walk_forward_config,
        )

        # Should fall back to predict()
        assert len(result["predictions"]) > 0
