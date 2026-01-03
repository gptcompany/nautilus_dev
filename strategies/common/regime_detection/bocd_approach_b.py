"""BOCD Approach B: Vectorized with Pre-allocated Arrays.

Optimized implementation using vectorized operations and fixed-size arrays.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy.special import gammaln

from strategies.common.regime_detection.config import BOCDConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray


class BOCD:
    """Bayesian Online Changepoint Detection (Adams & MacKay 2007).

    Vectorized implementation with pre-allocated arrays for performance.
    Uses Student-t conjugate prior with log-space PDF for numerical stability.
    """

    def __init__(self, config: BOCDConfig | None = None) -> None:
        """Initialize BOCD detector.

        Args:
            config: BOCD configuration. Uses defaults if None.
        """
        self.config = config or BOCDConfig()

        # Prior parameters
        self._mu0 = self.config.mu0
        self._kappa0 = self.config.kappa0
        self._alpha0 = self.config.alpha0
        self._beta0 = self.config.beta0
        self._hazard = self.config.hazard_rate
        self._max_rl = self.config.max_run_length

        # Pre-allocate arrays for performance
        self._mu = np.zeros(self._max_rl + 1)
        self._kappa = np.zeros(self._max_rl + 1)
        self._alpha = np.zeros(self._max_rl + 1)
        self._beta = np.zeros(self._max_rl + 1)
        self._run_length_dist = np.zeros(self._max_rl + 1)

        self.reset()

    def reset(self) -> None:
        """Reset detector to initial state."""
        self.t = 0
        self._active_len = 1  # How many run lengths are currently active

        # Initialize with prior
        self._mu.fill(0)
        self._kappa.fill(0)
        self._alpha.fill(0)
        self._beta.fill(0)
        self._run_length_dist.fill(0)

        self._mu[0] = self._mu0
        self._kappa[0] = self._kappa0
        self._alpha[0] = self._alpha0
        self._beta[0] = self._beta0
        self._run_length_dist[0] = 1.0

    def update(self, observation: float) -> float:
        """Process a single observation.

        Args:
            observation: New data point (e.g., return).

        Returns:
            Changepoint probability P(r_t = 0).
        """
        self.t += 1
        x = observation
        n = self._active_len

        # Step 1: Vectorized predictive probabilities (Student-t)
        pred_probs = self._vectorized_student_t_pdf(x, n)

        # Step 2: Growth probabilities (no changepoint)
        growth = self._run_length_dist[:n] * pred_probs * (1 - self._hazard)

        # Step 3: Changepoint probability
        cp_prob = np.sum(self._run_length_dist[:n] * pred_probs * self._hazard)

        # Step 4: Update run length distribution
        new_active_len = min(n + 1, self._max_rl + 1)

        # Shift growth probabilities
        self._run_length_dist[1:new_active_len] = growth[: new_active_len - 1]
        self._run_length_dist[0] = cp_prob

        # Zero out inactive slots
        if new_active_len < len(self._run_length_dist):
            self._run_length_dist[new_active_len:] = 0

        # Normalize
        total = np.sum(self._run_length_dist[:new_active_len])
        if total > 1e-300:
            self._run_length_dist[:new_active_len] /= total
        else:
            # Numerical issue - reset
            self._run_length_dist[:new_active_len] = 1.0 / new_active_len

        # Step 5: Update sufficient statistics (vectorized)
        self._vectorized_update_stats(x, n, new_active_len)

        self._active_len = new_active_len

        return float(self._run_length_dist[0])

    def _vectorized_student_t_pdf(self, x: float, n: int) -> NDArray[np.floating]:
        """Vectorized Student-t PDF computation.

        Uses log-space computation for numerical stability.

        Args:
            x: Observation.
            n: Number of active run lengths.

        Returns:
            Array of PDF values.
        """
        mu = self._mu[:n]
        kappa = self._kappa[:n]
        alpha = self._alpha[:n]
        beta = self._beta[:n]

        # Degrees of freedom
        df = 2 * alpha

        # Scale parameter
        scale = np.sqrt(beta * (kappa + 1) / (alpha * kappa))

        # Standardized value
        z = (x - mu) / scale

        # Log PDF of Student-t
        log_pdf = (
            gammaln((df + 1) / 2)
            - gammaln(df / 2)
            - 0.5 * np.log(df * np.pi)
            - np.log(scale)
            - ((df + 1) / 2) * np.log(1 + z**2 / df)
        )

        # Handle numerical issues
        log_pdf = np.clip(log_pdf, -700, 700)

        return np.exp(log_pdf)

    def _vectorized_update_stats(self, x: float, old_n: int, new_n: int) -> None:
        """Vectorized update of sufficient statistics.

        Args:
            x: Observation.
            old_n: Previous number of active run lengths.
            new_n: New number of active run lengths.
        """
        # Save old values for update
        mu_old = self._mu[:old_n].copy()
        kappa_old = self._kappa[:old_n].copy()
        alpha_old = self._alpha[:old_n].copy()
        beta_old = self._beta[:old_n].copy()

        # New run length 0 gets prior
        self._mu[0] = self._mu0
        self._kappa[0] = self._kappa0
        self._alpha[0] = self._alpha0
        self._beta[0] = self._beta0

        # Shift and update existing run lengths
        copy_len = min(old_n, new_n - 1)
        if copy_len > 0:
            # Bayesian update formulas (vectorized)
            kappa_new = kappa_old[:copy_len] + 1
            mu_new = (kappa_old[:copy_len] * mu_old[:copy_len] + x) / kappa_new
            alpha_new = alpha_old[:copy_len] + 0.5
            beta_new = (
                beta_old[:copy_len]
                + 0.5 * kappa_old[:copy_len] * (x - mu_old[:copy_len]) ** 2 / kappa_new
            )

            self._mu[1 : copy_len + 1] = mu_new
            self._kappa[1 : copy_len + 1] = kappa_new
            self._alpha[1 : copy_len + 1] = alpha_new
            self._beta[1 : copy_len + 1] = beta_new

    def get_changepoint_probability(self) -> float:
        """Get probability that a changepoint just occurred.

        Returns:
            P(r_t = 0) at current step.
        """
        return float(self._run_length_dist[0])

    def get_run_length_distribution(self) -> NDArray[np.floating]:
        """Get full posterior over run lengths.

        Returns:
            Array of P(run_length = r) for r in [0, t].
        """
        return self._run_length_dist[: self._active_len].copy()

    def is_changepoint(self, threshold: float | None = None) -> bool:
        """Check if changepoint detected above threshold.

        Args:
            threshold: Detection threshold. Uses config default if None.

        Returns:
            True if P(changepoint) > threshold.
        """
        if threshold is None:
            threshold = self.config.detection_threshold
        return self.get_changepoint_probability() > threshold
