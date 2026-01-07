"""HMM Regime Detection Filter - Approach D: Ensemble (Best of B + C).

Strategy: Feature normalization + multi-init + diagonal covariance for stability
Complexity: O(n * n_iter * n_init) for fitting, O(1) for prediction
Trade-offs:
  + Feature normalization improves HMM convergence (from C)
  + Multiple random initializations for robustness (from B)
  + Diagonal covariance reduces overfitting and improves stability
  + Proper handling of degenerate cases
  - Slightly slower due to multi-init
"""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import numpy as np
from hmmlearn.hmm import GaussianHMM
from sklearn.preprocessing import StandardScaler

from strategies.common.regime_detection.types import RegimeState

if TYPE_CHECKING:
    from numpy.typing import NDArray


class HMMRegimeFilter:
    """Hidden Markov Model filter for market regime detection.

    Uses Gaussian HMM with feature normalization and multiple random
    initializations for robust regime detection. Uses diagonal covariance
    for numerical stability.

    Attributes:
        n_states: Number of hidden states in the HMM.
        n_iter: Maximum iterations for EM algorithm.
        n_init: Number of random initializations.
        min_samples: Minimum samples required for fitting.
        is_fitted: Whether the model has been fitted.
        model: The underlying GaussianHMM model.
        best_score: Log-likelihood score of best model.
    """

    def __init__(
        self,
        n_states: int = 3,
        n_iter: int = 100,
        n_init: int = 10,
        min_samples: int = 100,
    ) -> None:
        """Initialize HMM regime filter.

        Args:
            n_states: Number of hidden states (2-5 recommended).
            n_iter: Maximum EM iterations per initialization.
            n_init: Number of random initializations to try.
            min_samples: Minimum samples required before fitting.
        """
        self.n_states = n_states
        self.n_iter = n_iter
        self.n_init = max(1, n_init)
        self.min_samples = min_samples

        self.is_fitted: bool = False
        self.model: GaussianHMM | None = None
        self.best_score: float | None = None

        # Feature normalization
        self._scaler: StandardScaler | None = None

        # Store ORIGINAL (unnormalized) state characteristics for regime mapping
        self._state_means: NDArray[np.floating] | None = None

    def fit(
        self,
        returns: NDArray[np.floating],
        volatility: NDArray[np.floating],
    ) -> None:
        """Fit HMM to historical returns and volatility data.

        Normalizes features before fitting and stores scaler for
        consistent prediction normalization. Uses diagonal covariance
        for numerical stability.

        Args:
            returns: Array of historical returns.
            volatility: Array of historical volatility values.

        Raises:
            ValueError: If data length is below min_samples.
        """
        if len(returns) < self.min_samples:
            raise ValueError(
                f"Insufficient data: {len(returns)} samples, minimum {self.min_samples} required"
            )

        # Stack features: [returns, volatility]
        features = np.column_stack([returns, volatility])

        # Normalize features for better HMM convergence
        self._scaler = StandardScaler()
        features_scaled = self._scaler.fit_transform(features)

        best_model: GaussianHMM | None = None
        best_score = float("-inf")

        # Try multiple random initializations
        for init_idx in range(self.n_init):
            # Use 'diag' covariance for stability (avoids positive-definite issues)
            model = GaussianHMM(
                n_components=self.n_states,
                covariance_type="diag",  # More stable than "full"
                n_iter=self.n_iter,
                random_state=init_idx * 42 + 7,  # Different seed per init
                tol=1e-4,
            )

            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    model.fit(features_scaled)
                    score = model.score(features_scaled)

                if score > best_score:
                    best_score = score
                    best_model = model
            except Exception:
                # Initialization failed, try next one
                continue

        if best_model is None:
            # Fallback: single deterministic init with more iterations
            best_model = GaussianHMM(
                n_components=self.n_states,
                covariance_type="diag",
                n_iter=self.n_iter * 2,
                random_state=42,
                tol=1e-4,
            )
            best_model.fit(features_scaled)
            best_score = best_model.score(features_scaled)

        self.model = best_model
        self.best_score = best_score

        # Convert normalized means back to original scale for regime mapping
        # This ensures from_hmm_state gets meaningful returns/volatility values
        self._state_means = self._scaler.inverse_transform(self.model.means_)

        self.is_fitted = True

    def predict(
        self,
        returns: float,
        volatility: float,
    ) -> RegimeState:
        """Predict current regime from single observation.

        Args:
            returns: Current return value.
            volatility: Current volatility value.

        Returns:
            The predicted RegimeState.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted or self.model is None or self._scaler is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        features = np.array([[returns, volatility]])
        features_scaled = self._scaler.transform(features)
        state_idx = int(self.model.predict(features_scaled)[0])

        return RegimeState.from_hmm_state(
            state_idx=state_idx,
            mean_returns=list(self._state_means[:, 0]),
            mean_volatility=list(self._state_means[:, 1]),
        )

    def get_state_probabilities(
        self,
        returns: float,
        volatility: float,
    ) -> NDArray[np.floating]:
        """Get probability distribution over states.

        Args:
            returns: Current return value.
            volatility: Current volatility value.

        Returns:
            Array of probabilities for each state.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted or self.model is None or self._scaler is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        features = np.array([[returns, volatility]])
        features_scaled = self._scaler.transform(features)
        _, posteriors = self.model.score_samples(features_scaled)
        return posteriors[0]
