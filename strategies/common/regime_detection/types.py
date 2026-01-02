"""Type definitions for regime detection.

Provides enums for regime states and volatility clusters.
"""

from __future__ import annotations

from enum import IntEnum


class RegimeState(IntEnum):
    """Market regime states detected by HMM.

    Values are ordered by expected volatility (low to high).
    """

    TRENDING_UP = 0
    """Upward trending market with consistent direction."""

    TRENDING_DOWN = 1
    """Downward trending market with consistent direction."""

    RANGING = 2
    """Sideways/consolidating market with no clear direction."""

    VOLATILE = 3
    """High volatility market with rapid directional changes."""

    @classmethod
    def from_hmm_state(
        cls,
        state_idx: int,
        mean_returns: list[float],
        mean_volatility: list[float],
    ) -> RegimeState:
        """Map HMM state index to regime state based on characteristics.

        Args:
            state_idx: The HMM state index (0 to n_states-1).
            mean_returns: Mean returns for each HMM state.
            mean_volatility: Mean volatility for each HMM state.

        Returns:
            The corresponding RegimeState.
        """
        n_states = len(mean_returns)
        ret = mean_returns[state_idx]

        # Sort states by volatility to identify high/low vol regimes
        vol_rank = sorted(range(n_states), key=lambda i: mean_volatility[i])
        high_vol_idx = vol_rank[-1]

        # High volatility state
        if state_idx == high_vol_idx and n_states >= 3:
            return cls.VOLATILE

        # Trending states based on return sign
        if ret > 0.0001:  # Small threshold to avoid noise
            return cls.TRENDING_UP
        elif ret < -0.0001:
            return cls.TRENDING_DOWN
        else:
            return cls.RANGING


class VolatilityCluster(IntEnum):
    """Volatility cluster states detected by GMM."""

    LOW = 0
    """Low volatility regime - tight price ranges."""

    MEDIUM = 1
    """Medium volatility regime - normal market conditions."""

    HIGH = 2
    """High volatility regime - wide price swings."""

    @classmethod
    def from_gmm_cluster(
        cls,
        cluster_idx: int,
        cluster_means: list[float],
    ) -> VolatilityCluster:
        """Map GMM cluster index to volatility cluster based on means.

        Args:
            cluster_idx: The GMM cluster index (0 to n_clusters-1).
            cluster_means: Mean volatility for each GMM cluster.

        Returns:
            The corresponding VolatilityCluster.
        """
        n_clusters = len(cluster_means)
        sorted_indices = sorted(range(n_clusters), key=lambda i: cluster_means[i])

        rank = sorted_indices.index(cluster_idx)

        if n_clusters == 3:
            return cls(rank)
        elif n_clusters == 2:
            return cls.LOW if rank == 0 else cls.HIGH
        else:
            # For n_clusters > 3, map to LOW/MEDIUM/HIGH based on terciles
            if rank < n_clusters / 3:
                return cls.LOW
            elif rank < 2 * n_clusters / 3:
                return cls.MEDIUM
            else:
                return cls.HIGH
