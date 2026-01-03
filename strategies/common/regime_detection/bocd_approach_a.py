"""BOCD Approach A: Standard Adams-MacKay with NumPy Arrays.

Direct implementation following the 2007 paper closely.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy.stats import t as student_t

from strategies.common.regime_detection.config import BOCDConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray


class BOCD:
    """Bayesian Online Changepoint Detection (Adams & MacKay 2007).

    Standard implementation using NumPy arrays for run length tracking.
    Uses Student-t conjugate prior for Gaussian observations with unknown
    mean and variance.
    """

    def __init__(self, config: BOCDConfig | None = None) -> None:
        """Initialize BOCD detector.

        Args:
            config: BOCD configuration. Uses defaults if None.
        """
        self.config = config or BOCDConfig()

        # Prior parameters (Normal-Inverse-Gamma conjugate prior)
        self._mu0 = self.config.mu0
        self._kappa0 = self.config.kappa0
        self._alpha0 = self.config.alpha0
        self._beta0 = self.config.beta0
        self._hazard = self.config.hazard_rate
        self._max_run_length = self.config.max_run_length

        # Initialize state
        self.reset()

    def reset(self) -> None:
        """Reset detector to initial state."""
        self.t = 0

        # Run length distribution: P(r_t | x_{1:t})
        # Initially, P(r_0 = 0) = 1
        self._run_length_dist: NDArray[np.floating] = np.array([1.0])

        # Sufficient statistics for each run length hypothesis
        # mu_r, kappa_r, alpha_r, beta_r for r = 0, 1, 2, ...
        self._mu: list[float] = [self._mu0]
        self._kappa: list[float] = [self._kappa0]
        self._alpha: list[float] = [self._alpha0]
        self._beta: list[float] = [self._beta0]

    def update(self, observation: float) -> float:
        """Process a single observation.

        Args:
            observation: New data point (e.g., return).

        Returns:
            Changepoint probability P(r_t = 0).
        """
        self.t += 1
        x = observation

        # Step 1: Calculate predictive probabilities for each run length
        pred_probs = self._predictive_probabilities(x)

        # Step 2: Calculate growth probabilities (no changepoint)
        # P(r_t = r+1 | x_{1:t}) proportional to P(r_{t-1} = r) * p(x_t | r) * (1 - H(r))
        growth_probs = self._run_length_dist * pred_probs * (1 - self._hazard)

        # Step 3: Calculate changepoint probability
        # P(r_t = 0 | x_{1:t}) proportional to sum over r of P(r_{t-1} = r) * p(x_t | r) * H(r)
        cp_prob = np.sum(self._run_length_dist * pred_probs * self._hazard)

        # Step 4: Build new run length distribution
        new_dist = np.zeros(min(self.t + 1, self._max_run_length + 1))
        new_dist[0] = cp_prob

        # Copy growth probabilities (with truncation if needed)
        copy_len = min(len(growth_probs), len(new_dist) - 1)
        new_dist[1 : copy_len + 1] = growth_probs[:copy_len]

        # Normalize
        total = np.sum(new_dist)
        if total > 0:
            new_dist /= total
        else:
            # Fallback: reset to uniform if numerical issues
            new_dist = np.ones_like(new_dist) / len(new_dist)

        self._run_length_dist = new_dist

        # Step 5: Update sufficient statistics
        self._update_sufficient_statistics(x)

        return float(new_dist[0])

    def _predictive_probabilities(self, x: float) -> NDArray[np.floating]:
        """Calculate predictive probability p(x_t | r) for each run length.

        Uses Student-t distribution with parameters derived from conjugate prior.

        Args:
            x: Observation.

        Returns:
            Array of predictive probabilities for each run length hypothesis.
        """
        n = len(self._run_length_dist)
        pred_probs = np.zeros(n)

        for r in range(n):
            # Student-t parameters from conjugate prior
            mu_r = self._mu[r]
            kappa_r = self._kappa[r]
            alpha_r = self._alpha[r]
            beta_r = self._beta[r]

            # Degrees of freedom
            df = 2 * alpha_r

            # Location and scale
            loc = mu_r
            scale = np.sqrt(beta_r * (kappa_r + 1) / (alpha_r * kappa_r))

            # Predictive probability
            pred_probs[r] = student_t.pdf(x, df=df, loc=loc, scale=scale)

        return pred_probs

    def _update_sufficient_statistics(self, x: float) -> None:
        """Update sufficient statistics for each run length hypothesis.

        Bayesian update for Normal-Inverse-Gamma conjugate prior.

        Args:
            x: Observation.
        """
        n = len(self._run_length_dist)

        # New parameters for r = 0 (changepoint just occurred)
        new_mu = [self._mu0]
        new_kappa = [self._kappa0]
        new_alpha = [self._alpha0]
        new_beta = [self._beta0]

        # Update parameters for existing run lengths
        for r in range(min(n - 1, self._max_run_length)):
            if r < len(self._mu):
                mu_r = self._mu[r]
                kappa_r = self._kappa[r]
                alpha_r = self._alpha[r]
                beta_r = self._beta[r]

                # Bayesian update formulas
                kappa_new = kappa_r + 1
                mu_new = (kappa_r * mu_r + x) / kappa_new
                alpha_new = alpha_r + 0.5
                beta_new = beta_r + 0.5 * kappa_r * (x - mu_r) ** 2 / kappa_new

                new_mu.append(mu_new)
                new_kappa.append(kappa_new)
                new_alpha.append(alpha_new)
                new_beta.append(beta_new)

        self._mu = new_mu
        self._kappa = new_kappa
        self._alpha = new_alpha
        self._beta = new_beta

    def get_changepoint_probability(self) -> float:
        """Get probability that a changepoint just occurred.

        Returns:
            P(r_t = 0) at current step.
        """
        if len(self._run_length_dist) == 0:
            return 0.0
        return float(self._run_length_dist[0])

    def get_run_length_distribution(self) -> NDArray[np.floating]:
        """Get full posterior over run lengths.

        Returns:
            Array of P(run_length = r) for r in [0, t].
        """
        return self._run_length_dist.copy()

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
