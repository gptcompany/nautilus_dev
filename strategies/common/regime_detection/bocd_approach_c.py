"""BOCD Approach C: Full Log-Space Computation.

Maximum numerical stability using log-space throughout.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
from scipy.special import gammaln

from strategies.common.regime_detection.config import BOCDConfig

if TYPE_CHECKING:
    from numpy.typing import NDArray


def _logsumexp(log_probs: NDArray[np.floating]) -> float:
    """Numerically stable log-sum-exp.

    Args:
        log_probs: Array of log probabilities.

    Returns:
        log(sum(exp(log_probs)))
    """
    max_val = np.max(log_probs)
    if np.isinf(max_val):
        return float("-inf")
    return float(max_val + np.log(np.sum(np.exp(log_probs - max_val))))


class BOCD:
    """Bayesian Online Changepoint Detection (Adams & MacKay 2007).

    Full log-space implementation for maximum numerical stability.
    Uses Student-t conjugate prior with all operations in log domain.
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

        # Log hazard for efficiency
        self._log_hazard = np.log(self.config.hazard_rate)
        self._log_1m_hazard = np.log(1 - self.config.hazard_rate)

        self._max_rl = self.config.max_run_length

        # Pre-allocate arrays
        self._mu = np.zeros(self._max_rl + 1)
        self._kappa = np.zeros(self._max_rl + 1)
        self._alpha = np.zeros(self._max_rl + 1)
        self._beta = np.zeros(self._max_rl + 1)

        # Log run length distribution (unnormalized)
        self._log_run_length = np.full(self._max_rl + 1, -np.inf)

        self.reset()

    def reset(self) -> None:
        """Reset detector to initial state."""
        self.t = 0
        self._active_len = 1

        # Initialize with prior
        self._mu.fill(0)
        self._kappa.fill(0)
        self._alpha.fill(0)
        self._beta.fill(0)

        self._mu[0] = self._mu0
        self._kappa[0] = self._kappa0
        self._alpha[0] = self._alpha0
        self._beta[0] = self._beta0

        # P(r_0 = 0) = 1 => log(1) = 0
        self._log_run_length.fill(-np.inf)
        self._log_run_length[0] = 0.0

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

        # Step 1: Log predictive probabilities (Student-t)
        log_pred = self._log_student_t_pdf(x, n)

        # Step 2: Log growth probabilities
        # log P(r_t = r+1) = log P(r_{t-1} = r) + log p(x|r) + log(1-H)
        log_growth = self._log_run_length[:n] + log_pred + self._log_1m_hazard

        # Step 3: Log changepoint probability (log-sum-exp for sum)
        # log P(r_t = 0) = log sum_r [P(r_{t-1}=r) * p(x|r) * H]
        log_cp_terms = self._log_run_length[:n] + log_pred + self._log_hazard
        log_cp_prob = _logsumexp(log_cp_terms)

        # Step 4: Update log run length distribution
        new_active_len = min(n + 1, self._max_rl + 1)

        # Shift growth probabilities
        new_log_rl = np.full(self._max_rl + 1, -np.inf)
        new_log_rl[0] = log_cp_prob
        copy_len = min(n, new_active_len - 1)
        if copy_len > 0:
            new_log_rl[1 : copy_len + 1] = log_growth[:copy_len]

        # Normalize (log-sum-exp trick)
        log_total = _logsumexp(new_log_rl[:new_active_len])
        if np.isfinite(log_total):
            new_log_rl[:new_active_len] -= log_total
        else:
            # Reset on numerical failure
            new_log_rl[:new_active_len] = -np.log(new_active_len)

        self._log_run_length = new_log_rl

        # Step 5: Update sufficient statistics
        self._update_stats(x, n, new_active_len)

        self._active_len = new_active_len

        return float(np.exp(self._log_run_length[0]))

    def _log_student_t_pdf(self, x: float, n: int) -> NDArray[np.floating]:
        """Log PDF of Student-t distribution (vectorized).

        Args:
            x: Observation.
            n: Number of active run lengths.

        Returns:
            Array of log PDF values.
        """
        mu = self._mu[:n]
        kappa = self._kappa[:n]
        alpha = self._alpha[:n]
        beta = self._beta[:n]

        # Degrees of freedom
        df = 2 * alpha

        # Scale parameter (protect against division by zero)
        kappa_safe = np.maximum(kappa, 1e-10)
        alpha_safe = np.maximum(alpha, 1e-10)
        beta_safe = np.maximum(beta, 1e-10)

        scale_sq = beta_safe * (kappa_safe + 1) / (alpha_safe * kappa_safe)
        scale = np.sqrt(scale_sq)

        # Standardized value
        z = (x - mu) / np.maximum(scale, 1e-10)

        # Log PDF of Student-t
        log_pdf = (
            gammaln((df + 1) / 2)
            - gammaln(df / 2)
            - 0.5 * np.log(df * np.pi)
            - np.log(np.maximum(scale, 1e-10))
            - ((df + 1) / 2) * np.log1p(z**2 / df)
        )

        # Clip extreme values
        return np.clip(log_pdf, -700, 0)

    def _update_stats(self, x: float, old_n: int, new_n: int) -> None:
        """Update sufficient statistics.

        Args:
            x: Observation.
            old_n: Previous number of active run lengths.
            new_n: New number of active run lengths.
        """
        # Save old values
        mu_old = self._mu[:old_n].copy()
        kappa_old = self._kappa[:old_n].copy()
        alpha_old = self._alpha[:old_n].copy()
        beta_old = self._beta[:old_n].copy()

        # New run length 0 gets prior
        self._mu[0] = self._mu0
        self._kappa[0] = self._kappa0
        self._alpha[0] = self._alpha0
        self._beta[0] = self._beta0

        # Update existing run lengths (Bayesian update)
        copy_len = min(old_n, new_n - 1)
        if copy_len > 0:
            kappa_new = kappa_old[:copy_len] + 1
            mu_new = (kappa_old[:copy_len] * mu_old[:copy_len] + x) / kappa_new
            alpha_new = alpha_old[:copy_len] + 0.5

            # Protect against numerical issues in beta update
            delta = x - mu_old[:copy_len]
            beta_new = (
                beta_old[:copy_len] + 0.5 * kappa_old[:copy_len] * delta**2 / kappa_new
            )

            # Ensure beta stays positive
            beta_new = np.maximum(beta_new, 1e-10)

            self._mu[1 : copy_len + 1] = mu_new
            self._kappa[1 : copy_len + 1] = kappa_new
            self._alpha[1 : copy_len + 1] = alpha_new
            self._beta[1 : copy_len + 1] = beta_new

    def get_changepoint_probability(self) -> float:
        """Get probability that a changepoint just occurred.

        Returns:
            P(r_t = 0) at current step.
        """
        log_prob = self._log_run_length[0]
        return float(np.exp(np.clip(log_prob, -700, 0)))

    def get_run_length_distribution(self) -> NDArray[np.floating]:
        """Get full posterior over run lengths.

        Returns:
            Array of P(run_length = r) for r in [0, t].
        """
        log_dist = self._log_run_length[: self._active_len]
        return np.exp(np.clip(log_dist, -700, 0))

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
