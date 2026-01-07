"""GMM Volatility Clustering Filter - Approach C: Sklearn Native Multi-Init.

Strategy: Use sklearn's built-in n_init parameter for multiple initializations
Complexity: O(n * n_iter * n_init) for fitting, O(1) for prediction
Trade-offs:
  + Leverages sklearn's optimized multi-init implementation
  + Clean, simple code that uses library features
  + No manual loop overhead
  + Automatic best model selection by sklearn
  - Less control over individual initialization behavior
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from sklearn.mixture import GaussianMixture

from strategies.common.regime_detection.types import VolatilityCluster

if TYPE_CHECKING:
    from numpy.typing import NDArray


class GMMVolatilityFilter:
    """Gaussian Mixture Model filter for volatility clustering.

    Uses sklearn's native multi-initialization for robust
    volatility clustering into LOW, MEDIUM, and HIGH states.

    Attributes:
        n_clusters: Number of volatility clusters.
        n_init: Number of initializations (passed to sklearn).
        min_samples: Minimum samples required for fitting.
        is_fitted: Whether the model has been fitted.
        model: The underlying GaussianMixture model.
        cluster_means: Mean volatility for each cluster.
    """

    def __init__(
        self,
        n_clusters: int = 3,
        n_init: int = 10,
        min_samples: int = 50,
    ) -> None:
        """Initialize GMM volatility filter.

        Args:
            n_clusters: Number of volatility clusters (typically 3).
            n_init: Number of random initializations (sklearn default: 1).
            min_samples: Minimum samples required before fitting.
        """
        self.n_clusters = n_clusters
        self.n_init = max(1, n_init)
        self.min_samples = min_samples

        self.is_fitted: bool = False
        self.model: GaussianMixture | None = None
        self._cluster_means: NDArray[np.floating] | None = None

    @property
    def cluster_means(self) -> list[float]:
        """Get the mean volatility for each cluster.

        Returns:
            List of mean volatility values, one per cluster.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted or self._cluster_means is None:
            raise RuntimeError("Model not fitted. Call fit() first.")
        return list(self._cluster_means.flatten())

    def fit(self, volatility: NDArray[np.floating]) -> None:
        """Fit GMM to historical volatility data.

        Uses sklearn's native n_init parameter for multiple
        initializations to find optimal clustering.

        Args:
            volatility: Array of historical volatility values.

        Raises:
            ValueError: If data length is below min_samples.
        """
        if len(volatility) < self.min_samples:
            raise ValueError(
                f"Insufficient data: {len(volatility)} samples, minimum {self.min_samples} required"
            )

        # Reshape to 2D for sklearn
        X = volatility.reshape(-1, 1)

        # Use sklearn's native multi-init
        self.model = GaussianMixture(
            n_components=self.n_clusters,
            covariance_type="full",
            n_init=self.n_init,  # Let sklearn handle multi-init
            init_params="k-means++",  # Better initialization
            random_state=42,
            max_iter=100,
            tol=1e-4,
        )
        self.model.fit(X)

        # Store cluster means for label mapping
        self._cluster_means = self.model.means_.flatten()
        self.is_fitted = True

    def predict(self, volatility: float) -> VolatilityCluster:
        """Predict volatility cluster for a single observation.

        Args:
            volatility: Current volatility value.

        Returns:
            The predicted VolatilityCluster.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X = np.array([[volatility]])
        cluster_idx = int(self.model.predict(X)[0])

        return VolatilityCluster.from_gmm_cluster(
            cluster_idx=cluster_idx,
            cluster_means=self.cluster_means,
        )

    def get_cluster_probabilities(
        self,
        volatility: float,
    ) -> NDArray[np.floating]:
        """Get probability distribution over clusters.

        Args:
            volatility: Current volatility value.

        Returns:
            Array of probabilities for each cluster.

        Raises:
            RuntimeError: If model is not fitted.
        """
        if not self.is_fitted or self.model is None:
            raise RuntimeError("Model not fitted. Call fit() first.")

        X = np.array([[volatility]])
        probs = self.model.predict_proba(X)
        result = probs[0]
        from typing import cast

        return cast(NDArray[np.floating], result)
