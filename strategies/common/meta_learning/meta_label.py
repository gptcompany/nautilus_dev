"""Meta-label generation for meta-learning pipeline.

This module provides the MetaLabelGenerator class that creates meta-labels
from primary model signals and true labels (from triple barrier labeling).

Meta-labels are binary: 1 if primary signal was correct, 0 if incorrect.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from numpy.typing import NDArray


class MetaLabelGenerator:
    """Generate meta-labels from primary signals and true labels.

    Meta-labels indicate whether the primary model's prediction was correct:
    - meta_label = 1 if primary_signal matches true_label (correct prediction)
    - meta_label = 0 if primary_signal does not match true_label (incorrect)
    - meta_label = 0 if primary_signal is 0 (no trade to evaluate)

    Example:
        >>> generator = MetaLabelGenerator()
        >>> signals = np.array([1, 1, -1, -1, 0])
        >>> labels = np.array([1, -1, -1, 1, 1])
        >>> meta_labels = generator.generate(signals, labels)
        >>> # meta_labels = [1, 0, 1, 0, 0]
    """

    def generate(
        self,
        primary_signals: NDArray[np.signedinteger],
        true_labels: NDArray[np.signedinteger],
    ) -> NDArray[np.signedinteger]:
        """Generate meta-labels from primary signals and true labels.

        Args:
            primary_signals: Primary model signals (+1 for long, -1 for short, 0 for no signal).
            true_labels: True labels from triple barrier labeling (+1 TP, -1 SL, 0 timeout).

        Returns:
            Array of meta-labels (1 for correct, 0 for incorrect).

        Raises:
            ValueError: If arrays have different lengths.
        """
        if len(primary_signals) != len(true_labels):
            msg = f"Array length mismatch: primary_signals={len(primary_signals)}, true_labels={len(true_labels)}"
            raise ValueError(msg)

        # Meta-label = 1 if signal matches label AND signal is not zero
        # Zero signals always get meta-label 0 (no trade to evaluate)
        matches = primary_signals == true_labels
        non_zero_signals = primary_signals != 0

        meta_labels = (matches & non_zero_signals).astype(np.int64)

        from typing import cast

        return cast(NDArray[np.signedinteger], meta_labels)

    def generate_with_mask(
        self,
        primary_signals: NDArray[np.signedinteger],
        true_labels: NDArray[np.signedinteger],
    ) -> tuple[NDArray[np.signedinteger], NDArray[np.bool_]]:
        """Generate meta-labels with mask for valid samples.

        Only samples where primary_signal != 0 are valid for training.

        Args:
            primary_signals: Primary model signals.
            true_labels: True labels from triple barrier labeling.

        Returns:
            Tuple of (meta_labels, valid_mask) where valid_mask indicates
            which samples have non-zero primary signals.
        """
        meta_labels = self.generate(primary_signals, true_labels)
        valid_mask = primary_signals != 0

        return meta_labels, valid_mask
