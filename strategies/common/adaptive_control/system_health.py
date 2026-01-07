"""
System Health Monitor - Trading Infrastructure State Machine

Simple state machine for monitoring trading system health.
No metaphors - just practical metrics and thresholds.
"""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Callable, Deque, Optional

import numpy as np

logger = logging.getLogger(__name__)


class HealthState(Enum):
    """System health states."""

    HEALTHY = "healthy"  # All systems nominal
    DEGRADED = "degraded"  # Some issues, reduce risk
    CRITICAL = "critical"  # Stop trading


@dataclass
class HealthMetrics:
    """Current system metrics snapshot."""

    timestamp: datetime
    latency_mean_ms: float
    latency_p99_ms: float
    rejection_rate: float  # 0.0 to 1.0
    slippage_bps: float  # Basis points
    drawdown_pct: float
    reconnects_1h: int
    state: HealthState
    score: float  # 0-100


class SystemHealthMonitor:
    """
    Monitors trading system health and provides risk multiplier.

    Usage:
        health = SystemHealthMonitor()

        # Record events
        health.record_latency(45.0)
        health.record_fill(slippage_bps=2.5)
        health.record_rejection()

        # Check state
        if health.state == HealthState.CRITICAL:
            strategy.halt()

        # Get risk multiplier
        size = base_size * health.risk_multiplier
    """

    def __init__(
        self,
        latency_threshold_ms: float = 100.0,
        rejection_threshold: float = 0.05,
        drawdown_halt_pct: float = 10.0,
    ):
        self.latency_threshold = latency_threshold_ms
        self.rejection_threshold = rejection_threshold
        self.drawdown_halt_pct = drawdown_halt_pct

        # Data stores (last hour)
        self._latencies: Deque[tuple[datetime, float]] = deque(maxlen=5000)
        self._fills: Deque[tuple[datetime, float]] = deque(maxlen=1000)
        self._rejections: Deque[datetime] = deque(maxlen=500)
        self._reconnects: Deque[datetime] = deque(maxlen=100)

        # Equity tracking
        self._peak_equity: float = 0.0
        self._current_equity: float = 0.0

        # Callbacks
        self._on_state_change: list[Callable] = []

        # Cached state
        self._last_state: Optional[HealthState] = None

    def record_latency(self, latency_ms: float) -> None:
        """Record order/message latency."""
        self._latencies.append((datetime.utcnow(), latency_ms))

    def record_fill(self, slippage_bps: float = 0.0) -> None:
        """Record successful fill with slippage."""
        self._fills.append((datetime.utcnow(), slippage_bps))

    def record_rejection(self) -> None:
        """Record order rejection."""
        self._rejections.append(datetime.utcnow())

    def record_reconnect(self) -> None:
        """Record connection drop/reconnect."""
        self._reconnects.append(datetime.utcnow())
        logger.warning("SystemHealth: Reconnection event")

    def set_equity(self, equity: float) -> None:
        """Update current equity for drawdown calculation."""
        self._current_equity = equity
        self._peak_equity = max(self._peak_equity, equity)

    def on_state_change(self, callback: Callable[[HealthState, HealthState], None]) -> None:
        """Register callback for state transitions."""
        self._on_state_change.append(callback)

    @property
    def drawdown_pct(self) -> float:
        """Current drawdown percentage."""
        if self._peak_equity <= 0:
            return 0.0
        return ((self._peak_equity - self._current_equity) / self._peak_equity) * 100

    def get_metrics(self) -> HealthMetrics:
        """Calculate current health metrics."""
        now = datetime.utcnow()
        cutoff = now - timedelta(hours=1)

        # Filter to 1-hour window
        latencies = [lat for ts, lat in self._latencies if ts > cutoff]
        fills = [slip for ts, slip in self._fills if ts > cutoff]
        rejections = [ts for ts in self._rejections if ts > cutoff]
        reconnects = [ts for ts in self._reconnects if ts > cutoff]

        # Calculate metrics
        if latencies:
            lat_arr = np.array(latencies)
            lat_mean = float(np.mean(lat_arr))
            lat_p99 = float(np.percentile(lat_arr, 99))
        else:
            lat_mean, lat_p99 = 0.0, 0.0

        total_orders = len(fills) + len(rejections)
        rejection_rate = len(rejections) / total_orders if total_orders > 0 else 0.0
        avg_slippage = float(np.mean(fills)) if fills else 0.0

        # Calculate score (0-100)
        score = 100.0
        if lat_mean > self.latency_threshold:
            score -= min(20, (lat_mean - self.latency_threshold) / 5)
        score -= rejection_rate * 50
        score -= abs(avg_slippage) * 2
        score -= min(30, self.drawdown_pct * 2)
        score -= len(reconnects) * 5
        score = max(0, min(100, score))

        # Determine state
        if score >= 70 and self.drawdown_pct < self.drawdown_halt_pct:
            state = HealthState.HEALTHY
        elif score >= 40 and self.drawdown_pct < self.drawdown_halt_pct:
            state = HealthState.DEGRADED
        else:
            state = HealthState.CRITICAL

        # Notify on state change
        if self._last_state and state != self._last_state:
            logger.warning(f"SystemHealth: {self._last_state.value} -> {state.value}")
            for cb in self._on_state_change:
                cb(self._last_state, state)
        self._last_state = state

        return HealthMetrics(
            timestamp=now,
            latency_mean_ms=lat_mean,
            latency_p99_ms=lat_p99,
            rejection_rate=rejection_rate,
            slippage_bps=avg_slippage,
            drawdown_pct=self.drawdown_pct,
            reconnects_1h=len(reconnects),
            state=state,
            score=score,
        )

    @property
    def state(self) -> HealthState:
        """Get current health state."""
        return self.get_metrics().state

    @property
    def risk_multiplier(self) -> float:
        """
        Risk multiplier based on health state.

        HEALTHY: 1.0 (full risk)
        DEGRADED: 0.5 (half risk)
        CRITICAL: 0.0 (no new positions)
        """
        state = self.state
        return {
            HealthState.HEALTHY: 1.0,
            HealthState.DEGRADED: 0.5,
            HealthState.CRITICAL: 0.0,
        }[state]

    def should_trade(self) -> tuple[bool, str]:
        """Check if trading should continue."""
        metrics = self.get_metrics()
        if metrics.state == HealthState.CRITICAL:
            return (
                False,
                f"CRITICAL: score={metrics.score:.0f}, dd={metrics.drawdown_pct:.1f}%",
            )
        return True, f"{metrics.state.value}: score={metrics.score:.0f}"
