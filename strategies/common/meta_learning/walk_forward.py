"""Walk-forward validation for meta-model training.

This module provides the WalkForwardSplitter class that generates
train/test splits with proper embargo and purging to prevent look-ahead bias.

Based on rigorous walk-forward validation protocol from academic literature:
- Rolling window (not expanding) for non-stationary markets
- Embargo gap between train and test to prevent leakage
- Purging of overlapping labels for triple barrier method
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

from strategies.common.meta_learning.config import WalkForwardConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray


class WalkForwardSplitter:
    """Walk-forward validation splitter with embargo and purging.

    Generates rolling train/test splits for time series data, ensuring
    no look-ahead bias through proper chronological ordering, embargo gaps,
    and optional purging of samples with overlapping labels.

    Attributes:
        config: WalkForwardConfig with window sizes and embargo.

    Example:
        >>> from strategies.common.meta_learning import WalkForwardSplitter, WalkForwardConfig
        >>> config = WalkForwardConfig(train_window=252, test_window=63, step_size=21, embargo_size=5)
        >>> splitter = WalkForwardSplitter(config)
        >>> splits = splitter.split(n_samples=500)
        >>> for train_idx, test_idx in splits:
        ...     model.fit(X[train_idx], y[train_idx])
        ...     score = model.score(X[test_idx], y[test_idx])
    """

    def __init__(self, config: WalkForwardConfig | None = None) -> None:
        """Initialize WalkForwardSplitter.

        Args:
            config: Configuration for walk-forward splits. Uses defaults if None.
        """
        self._config = config or WalkForwardConfig()

    @property
    def config(self) -> WalkForwardConfig:
        """Get configuration."""
        return self._config

    def split(
        self,
        n_samples: int,
    ) -> list[tuple[NDArray[np.intp], NDArray[np.intp]]]:
        """Generate train/test index pairs.

        Creates rolling window splits where each split has:
        - train_window bars for training
        - embargo_size bars gap (excluded from both)
        - test_window bars for testing

        Args:
            n_samples: Total number of samples in the dataset.

        Returns:
            List of (train_indices, test_indices) tuples.
            Each array contains consecutive integer indices.

        Note:
            The last split may have fewer test samples if the data ends early.
        """
        splits = []

        # Minimum samples needed for one complete split
        min_required = (
            self._config.train_window
            + self._config.embargo_size
            + self._config.test_window
        )

        if n_samples < min_required:
            # Not enough data for even one split
            return splits

        # Starting position
        i = 0

        while True:
            train_start = i
            train_end = i + self._config.train_window

            # Check if we have room for embargo + at least 1 test sample
            if train_end + self._config.embargo_size >= n_samples:
                break

            test_start = train_end + self._config.embargo_size
            test_end = min(test_start + self._config.test_window, n_samples)

            # Need at least 1 test sample
            if test_start >= n_samples:
                break

            train_idx = np.arange(train_start, train_end, dtype=np.intp)
            test_idx = np.arange(test_start, test_end, dtype=np.intp)

            splits.append((train_idx, test_idx))

            # Move forward by step_size
            i += self._config.step_size

            # Check if next split is possible
            if i + self._config.train_window + self._config.embargo_size >= n_samples:
                break

        return splits

    def purge_splits(
        self,
        splits: list[tuple[NDArray[np.intp], NDArray[np.intp]]],
        max_holding_bars: int,
    ) -> list[tuple[NDArray[np.intp], NDArray[np.intp]]]:
        """Purge training samples whose labels overlap with test period.

        For triple barrier labeling, labels depend on future prices up to
        max_holding_bars ahead. This method removes training samples whose
        label calculation window extends into the test period.

        Args:
            splits: List of (train_indices, test_indices) from split().
            max_holding_bars: Maximum holding period for triple barrier labels.

        Returns:
            List of purged (train_indices, test_indices) tuples.
            Training sets will be smaller to ensure no look-ahead.

        Example:
            >>> splits = splitter.split(500)
            >>> purged = splitter.purge_splits(splits, max_holding_bars=10)
        """
        purged_splits = []

        for train_idx, test_idx in splits:
            if len(train_idx) == 0 or len(test_idx) == 0:
                purged_splits.append((train_idx, test_idx))
                continue

            # Find the first test index
            first_test = test_idx[0]

            # Purge training samples whose label window overlaps with test
            # A sample at index i has label depending on data up to i + max_holding_bars
            # So we need: i + max_holding_bars < first_test
            # Which means: i < first_test - max_holding_bars
            max_safe_train = first_test - max_holding_bars

            # Filter training indices
            purged_train = train_idx[train_idx < max_safe_train]

            purged_splits.append((purged_train, test_idx))

        return purged_splits

    def get_n_splits(self, n_samples: int) -> int:
        """Get the number of splits that would be generated.

        Args:
            n_samples: Total number of samples.

        Returns:
            Number of train/test splits.
        """
        return len(self.split(n_samples))


def walk_forward_train(
    model,
    features: NDArray[np.floating],
    meta_labels: NDArray[np.signedinteger],
    config: WalkForwardConfig | None = None,
    max_holding_bars: int | None = None,
) -> dict:
    """Train model using walk-forward validation.

    Utility function that handles the complete walk-forward training loop.

    Args:
        model: Model with fit() and predict_proba() methods.
        features: Feature matrix (n_samples, n_features).
        meta_labels: Target labels.
        config: Walk-forward configuration.
        max_holding_bars: If provided, applies purging for triple barrier labels.

    Returns:
        Dictionary with:
        - 'predictions': Out-of-sample predictions for each test period
        - 'actuals': Actual labels for each test period
        - 'indices': Test indices for each split
        - 'n_splits': Number of walk-forward splits
    """
    splitter = WalkForwardSplitter(config)
    splits = splitter.split(len(features))

    if max_holding_bars is not None:
        splits = splitter.purge_splits(splits, max_holding_bars)

    all_predictions = []
    all_actuals = []
    all_indices = []

    for train_idx, test_idx in splits:
        if len(train_idx) == 0 or len(test_idx) == 0:
            continue

        # Fit on training data
        model.fit(features[train_idx], meta_labels[train_idx])

        # Predict on test data
        if hasattr(model, "predict_proba"):
            preds = model.predict_proba(features[test_idx])
            if preds.ndim == 2:
                preds = preds[:, 1]  # Get positive class probability
        else:
            preds = model.predict(features[test_idx])

        all_predictions.extend(preds)
        all_actuals.extend(meta_labels[test_idx])
        all_indices.extend(test_idx)

    return {
        "predictions": np.array(all_predictions),
        "actuals": np.array(all_actuals),
        "indices": np.array(all_indices),
        "n_splits": len(splits),
    }
