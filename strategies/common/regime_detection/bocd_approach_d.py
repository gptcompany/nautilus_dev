"""BOCD Approach D: Correct Message Passing per Adams & MacKay 2007.

The key insight is that we track joint probabilities P(r_t, x_{1:t}),
not marginal P(r_t | x_{1:t}). Normalization happens only when queried.
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

    Correct implementation tracking joint probabilities.
    Uses Student-t conjugate prior for Gaussian observations with
    unknown mean and variance.
    """

    def __init__(self, config: BOCDConfig | None = None) -> None:
        """Initialize BOCD detector.

        Args:
            config: BOCD configuration. Uses defaults if None.
        """
        self.config = config or BOCDConfig()

        # Prior parameters (Normal-Inverse-Gamma)
        self._mu0 = self.config.mu0
        self._kappa0 = self.config.kappa0
        self._alpha0 = self.config.alpha0
        self._beta0 = self.config.beta0
        self._hazard = self.config.hazard_rate
        self._max_rl = self.config.max_run_length

        # Pre-allocate arrays
        self._mu = np.zeros(self._max_rl + 2)
        self._kappa = np.zeros(self._max_rl + 2)
        self._alpha = np.zeros(self._max_rl + 2)
        self._beta = np.zeros(self._max_rl + 2)

        # Joint probability P(r_t, x_{1:t}) - NOT normalized!
        # This is the key difference from the buggy implementations
        self._joint = np.zeros(self._max_rl + 2)

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
        self._joint.fill(0)

        self._mu[0] = self._mu0
        self._kappa[0] = self._kappa0
        self._alpha[0] = self._alpha0
        self._beta[0] = self._beta0

        # P(r_0 = 0) = 1 (start with run length 0)
        self._joint[0] = 1.0

    def update(self, observation: float) -> float:
        """Process a single observation.

        Args:
            observation: New data point (e.g., return).

        Returns:
            Changepoint probability P(r_t = 0 | x_{1:t}).
        """
        self.t += 1
        x = observation
        n = self._active_len

        # Step 1: Compute predictive probabilities for each run length
        pred_probs = self._student_t_pdf(x, n)

        # Step 2: Compute joint probabilities P(r_t, x_{1:t})
        # Using the recursion from Adams & MacKay 2007

        # Growth: P(r_t = r+1, x_{1:t}) = P(r_{t-1}=r, x_{1:t-1}) * (1-H) * pi(x_t | r)
        growth = self._joint[:n] * pred_probs * (1 - self._hazard)

        # Changepoint: P(r_t = 0, x_{1:t}) = sum_r P(r_{t-1}=r, x_{1:t-1}) * H * pi(x_t | r)
        cp_joint = np.sum(self._joint[:n] * pred_probs * self._hazard)

        # Step 3: Update joint distribution
        new_n = min(n + 1, self._max_rl + 1)

        # Shift growth probabilities (r+1 gets mass from r)
        new_joint = np.zeros_like(self._joint)
        new_joint[0] = cp_joint
        new_joint[1:new_n] = growth[: new_n - 1]

        self._joint = new_joint

        # Step 4: Update sufficient statistics
        self._update_stats(x, n, new_n)

        self._active_len = new_n

        # Return normalized changepoint probability
        total = np.sum(self._joint[:new_n])
        if total > 1e-300:
            return float(cp_joint / total)
        return 0.0

    def _student_t_pdf(self, x: float, n: int) -> NDArray[np.floating]:
        """Compute Student-t predictive PDF for each run length.

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

        # Degrees of freedom: 2 * alpha
        df = 2 * alpha

        # Scale parameter: sqrt(beta * (kappa + 1) / (alpha * kappa))
        # Protect against division by zero
        kappa_safe = np.maximum(kappa, 1e-10)
        alpha_safe = np.maximum(alpha, 1e-10)
        beta_safe = np.maximum(beta, 1e-10)

        scale_sq = beta_safe * (kappa_safe + 1) / (alpha_safe * kappa_safe)
        scale = np.sqrt(scale_sq)

        # Standardized value
        z = (x - mu) / np.maximum(scale, 1e-10)

        # Log PDF for numerical stability
        log_pdf = (
            gammaln((df + 1) / 2)
            - gammaln(df / 2)
            - 0.5 * np.log(df * np.pi)
            - np.log(np.maximum(scale, 1e-10))
            - ((df + 1) / 2) * np.log1p(z**2 / df)
        )

        return np.exp(np.clip(log_pdf, -700, 0))

    def _update_stats(self, x: float, old_n: int, new_n: int) -> None:
        """Update sufficient statistics for Bayesian posterior.

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

        # Run length 0 always uses prior (fresh start after changepoint)
        self._mu[0] = self._mu0
        self._kappa[0] = self._kappa0
        self._alpha[0] = self._alpha0
        self._beta[0] = self._beta0

        # Update statistics for run lengths 1, 2, ..., new_n-1
        # These come from run lengths 0, 1, ..., old_n-1 respectively
        copy_len = min(old_n, new_n - 1)
        if copy_len > 0:
            # Bayesian update formulas for Normal-Inverse-Gamma
            kappa_new = kappa_old[:copy_len] + 1
            mu_new = (kappa_old[:copy_len] * mu_old[:copy_len] + x) / kappa_new
            alpha_new = alpha_old[:copy_len] + 0.5
            delta = x - mu_old[:copy_len]
            beta_new = (
                beta_old[:copy_len] + 0.5 * kappa_old[:copy_len] * delta**2 / kappa_new
            )

            self._mu[1 : copy_len + 1] = mu_new
            self._kappa[1 : copy_len + 1] = kappa_new
            self._alpha[1 : copy_len + 1] = alpha_new
            self._beta[1 : copy_len + 1] = np.maximum(beta_new, 1e-10)

    def get_changepoint_probability(self) -> float:
        """Get probability that a changepoint just occurred.

        Returns:
            P(r_t = 0 | x_{1:t}) at current step.
        """
        n = self._active_len
        total = np.sum(self._joint[:n])
        if total > 1e-300:
            return float(self._joint[0] / total)
        return 0.0

    def get_run_length_distribution(self) -> NDArray[np.floating]:
        """Get full posterior over run lengths.

        Returns:
            Normalized array of P(run_length = r | x_{1:t}).
        """
        n = self._active_len
        joint = self._joint[:n].copy()
        total = np.sum(joint)
        if total > 1e-300:
            return joint / total
        return np.ones(n) / n

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
