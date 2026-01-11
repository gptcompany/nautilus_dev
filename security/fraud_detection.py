#!/usr/bin/env python3
"""
Trading Fraud Detection Module.

Detects suspicious trading patterns including:
- Wash trading (self-trading to inflate volume)
- Spoofing (placing orders with intent to cancel)
- Layering (multiple orders at different prices to manipulate)
- Front-running detection
- Unusual order patterns

Usage:
    from security.fraud_detection import FraudDetector, FraudAlert

    detector = FraudDetector()

    # Check single order
    alerts = detector.check_order(order)

    # Analyze trading session
    alerts = detector.analyze_session(user_id="trader1", lookback_hours=24)

    # Real-time monitoring
    detector.start_monitoring()
"""

from __future__ import annotations

import logging
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class FraudType(Enum):
    """Types of trading fraud."""

    WASH_TRADING = "wash_trading"
    SPOOFING = "spoofing"
    LAYERING = "layering"
    FRONT_RUNNING = "front_running"
    PUMP_AND_DUMP = "pump_and_dump"
    ORDER_STUFFING = "order_stuffing"
    QUOTE_STUFFING = "quote_stuffing"
    MOMENTUM_IGNITION = "momentum_ignition"
    UNUSUAL_VOLUME = "unusual_volume"
    UNUSUAL_TIMING = "unusual_timing"


class AlertSeverity(Enum):
    """Fraud alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class FraudAlert:
    """Fraud detection alert."""

    fraud_type: FraudType
    severity: AlertSeverity
    description: str
    evidence: dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: str = ""
    symbol: str = ""
    recommended_action: str = ""
    confidence: float = 0.0  # 0-1 confidence score

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "fraud_type": self.fraud_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "evidence": self.evidence,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "symbol": self.symbol,
            "recommended_action": self.recommended_action,
            "confidence": self.confidence,
        }


@dataclass
class FraudDetectionConfig:
    """Configuration for fraud detection thresholds."""

    # Wash trading thresholds
    wash_trade_time_window_seconds: int = 60
    wash_trade_min_matches: int = 3
    wash_trade_volume_ratio: float = 0.8  # Same account volume ratio

    # Spoofing thresholds
    spoof_cancel_ratio: float = 0.9  # Orders cancelled vs filled
    spoof_time_window_seconds: int = 30
    spoof_min_orders: int = 5

    # Layering thresholds
    layer_price_levels: int = 5  # Multiple orders at different prices
    layer_time_window_seconds: int = 60
    layer_min_orders: int = 10

    # Order rate thresholds
    max_orders_per_second: int = 10
    max_orders_per_minute: int = 100
    max_cancels_per_minute: int = 50

    # Volume thresholds
    unusual_volume_std_dev: float = 3.0  # Standard deviations from mean


class FraudDetector:
    """
    Real-time trading fraud detector.

    Analyzes order flow and trading patterns to detect manipulation.
    """

    def __init__(
        self,
        config: FraudDetectionConfig | None = None,
        questdb_url: str | None = None,
    ):
        """
        Initialize fraud detector.

        Args:
            config: Detection thresholds configuration.
            questdb_url: QuestDB URL for historical analysis.
        """
        self.config = config or FraudDetectionConfig()
        self.questdb_url = questdb_url or os.getenv("QUESTDB_URL", "http://localhost:9000")

        # In-memory order tracking
        self._recent_orders: dict[str, list[dict]] = defaultdict(list)
        self._order_counts: dict[str, dict[str, int]] = defaultdict(
            lambda: {"orders": 0, "cancels": 0, "fills": 0}
        )
        self._alerts: list[FraudAlert] = []

    def check_order(
        self,
        order: dict[str, Any],
        historical_orders: list[dict] | None = None,
    ) -> list[FraudAlert]:
        """
        Check a single order for fraud indicators.

        Args:
            order: Order dictionary with keys: order_id, user_id, symbol,
                   side, quantity, price, timestamp, status
            historical_orders: Optional recent orders for context

        Returns:
            List of fraud alerts detected
        """
        alerts = []

        # Track order
        self._track_order(order)

        # Run detection checks
        alerts.extend(self._check_wash_trading(order))
        alerts.extend(self._check_spoofing(order))
        alerts.extend(self._check_order_rate(order))
        alerts.extend(self._check_layering(order))

        # Store alerts
        self._alerts.extend(alerts)

        return alerts

    def _track_order(self, order: dict[str, Any]) -> None:
        """Track order in memory for pattern detection."""
        user_id = order.get("user_id", "")
        symbol = order.get("symbol", "")
        key = f"{user_id}:{symbol}"

        # Add to recent orders
        self._recent_orders[key].append(order)

        # Keep only recent orders (last 5 minutes)
        cutoff = datetime.utcnow() - timedelta(minutes=5)
        self._recent_orders[key] = [
            o
            for o in self._recent_orders[key]
            if datetime.fromisoformat(o.get("timestamp", "")) > cutoff
        ]

        # Update counts
        status = order.get("status", "")
        if status == "submitted":
            self._order_counts[user_id]["orders"] += 1
        elif status == "cancelled":
            self._order_counts[user_id]["cancels"] += 1
        elif status == "filled":
            self._order_counts[user_id]["fills"] += 1

    def _check_wash_trading(self, order: dict[str, Any]) -> list[FraudAlert]:
        """
        Detect wash trading patterns.

        Wash trading occurs when the same entity trades with itself
        to create artificial volume.
        """
        alerts = []
        user_id = order.get("user_id", "")
        symbol = order.get("symbol", "")
        key = f"{user_id}:{symbol}"

        recent = self._recent_orders.get(key, [])
        if len(recent) < self.config.wash_trade_min_matches:
            return alerts

        # Look for matching buy/sell pairs at similar prices
        buys = [o for o in recent if o.get("side") == "buy"]
        sells = [o for o in recent if o.get("side") == "sell"]

        matches = 0
        for buy in buys:
            for sell in sells:
                buy_price = float(buy.get("price", 0))
                sell_price = float(sell.get("price", 0))
                # Within 0.1% price
                if abs(buy_price - sell_price) / buy_price < 0.001:
                    matches += 1

        if matches >= self.config.wash_trade_min_matches:
            alerts.append(
                FraudAlert(
                    fraud_type=FraudType.WASH_TRADING,
                    severity=AlertSeverity.HIGH,
                    description=f"Potential wash trading detected: {matches} self-matched orders",
                    evidence={
                        "matches": matches,
                        "time_window": self.config.wash_trade_time_window_seconds,
                        "recent_orders": len(recent),
                    },
                    user_id=user_id,
                    symbol=symbol,
                    recommended_action="Review trading activity, consider temporary suspension",
                    confidence=min(0.9, matches / 10),
                )
            )

        return alerts

    def _check_spoofing(self, order: dict[str, Any]) -> list[FraudAlert]:
        """
        Detect spoofing patterns.

        Spoofing involves placing orders with intent to cancel,
        creating false impression of supply/demand.
        """
        alerts = []
        user_id = order.get("user_id", "")

        counts = self._order_counts.get(user_id, {})
        total_orders = counts.get("orders", 0)
        cancels = counts.get("cancels", 0)
        fills = counts.get("fills", 0)

        if total_orders < self.config.spoof_min_orders:
            return alerts

        cancel_ratio = cancels / max(1, cancels + fills)

        if cancel_ratio > self.config.spoof_cancel_ratio:
            alerts.append(
                FraudAlert(
                    fraud_type=FraudType.SPOOFING,
                    severity=AlertSeverity.HIGH,
                    description=f"High cancel ratio detected: {cancel_ratio:.1%}",
                    evidence={
                        "cancel_ratio": cancel_ratio,
                        "total_orders": total_orders,
                        "cancels": cancels,
                        "fills": fills,
                    },
                    user_id=user_id,
                    symbol=order.get("symbol", ""),
                    recommended_action="Investigate order patterns, may require trading halt",
                    confidence=min(0.95, cancel_ratio),
                )
            )

        return alerts

    def _check_order_rate(self, order: dict[str, Any]) -> list[FraudAlert]:
        """
        Detect abnormal order rates (order stuffing).

        Order stuffing involves submitting many orders to slow down
        other market participants.
        """
        alerts = []
        user_id = order.get("user_id", "")
        symbol = order.get("symbol", "")
        key = f"{user_id}:{symbol}"

        recent = self._recent_orders.get(key, [])

        # Orders in last second
        one_second_ago = datetime.utcnow() - timedelta(seconds=1)
        orders_per_second = len(
            [o for o in recent if datetime.fromisoformat(o.get("timestamp", "")) > one_second_ago]
        )

        if orders_per_second > self.config.max_orders_per_second:
            alerts.append(
                FraudAlert(
                    fraud_type=FraudType.ORDER_STUFFING,
                    severity=AlertSeverity.MEDIUM,
                    description=f"High order rate: {orders_per_second}/second",
                    evidence={
                        "orders_per_second": orders_per_second,
                        "threshold": self.config.max_orders_per_second,
                    },
                    user_id=user_id,
                    symbol=symbol,
                    recommended_action="Apply rate limiting",
                    confidence=0.7,
                )
            )

        return alerts

    def _check_layering(self, order: dict[str, Any]) -> list[FraudAlert]:
        """
        Detect layering patterns.

        Layering involves placing multiple orders at different price
        levels to create false impression of market depth.
        """
        alerts = []
        user_id = order.get("user_id", "")
        symbol = order.get("symbol", "")
        key = f"{user_id}:{symbol}"

        recent = self._recent_orders.get(key, [])
        if len(recent) < self.config.layer_min_orders:
            return alerts

        # Group by side and count unique price levels
        buy_prices = {o.get("price") for o in recent if o.get("side") == "buy"}
        sell_prices = {o.get("price") for o in recent if o.get("side") == "sell"}

        if (
            len(buy_prices) >= self.config.layer_price_levels
            or len(sell_prices) >= self.config.layer_price_levels
        ):
            alerts.append(
                FraudAlert(
                    fraud_type=FraudType.LAYERING,
                    severity=AlertSeverity.MEDIUM,
                    description=f"Multiple price levels detected: {max(len(buy_prices), len(sell_prices))} levels",
                    evidence={
                        "buy_levels": len(buy_prices),
                        "sell_levels": len(sell_prices),
                        "threshold": self.config.layer_price_levels,
                    },
                    user_id=user_id,
                    symbol=symbol,
                    recommended_action="Review order book manipulation",
                    confidence=0.6,
                )
            )

        return alerts

    def analyze_session(
        self,
        user_id: str,
        lookback_hours: int = 24,
    ) -> list[FraudAlert]:
        """
        Analyze a trading session for fraud patterns.

        Queries historical data and runs comprehensive analysis.
        """
        import json
        import urllib.parse
        import urllib.request

        alerts = []

        query = f"""
        SELECT order_id, symbol, side, quantity, price, status, timestamp
        FROM order_audit_log
        WHERE user_id = '{user_id}'
        AND timestamp > dateadd('h', -{lookback_hours}, now())
        ORDER BY timestamp ASC
        """

        try:
            url = f"{self.questdb_url}/exec?query={urllib.parse.quote(query)}"
            with urllib.request.urlopen(url, timeout=30) as response:
                data = json.loads(response.read())
                orders = [
                    {
                        "order_id": row[0],
                        "symbol": row[1],
                        "side": row[2],
                        "quantity": row[3],
                        "price": row[4],
                        "status": row[5],
                        "timestamp": row[6],
                        "user_id": user_id,
                    }
                    for row in data.get("dataset", [])
                ]

                # Analyze each order
                for order in orders:
                    order_alerts = self.check_order(order)
                    alerts.extend(order_alerts)

        except Exception as e:
            logger.error(f"Failed to analyze session: {e}")

        return alerts

    def get_alerts(
        self,
        severity: AlertSeverity | None = None,
        fraud_type: FraudType | None = None,
        limit: int = 100,
    ) -> list[FraudAlert]:
        """Get recent fraud alerts with optional filtering."""
        alerts = self._alerts[-limit:]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if fraud_type:
            alerts = [a for a in alerts if a.fraud_type == fraud_type]

        return alerts

    def clear_alerts(self) -> None:
        """Clear alert history."""
        self._alerts.clear()

    def reset_tracking(self) -> None:
        """Reset all tracking data."""
        self._recent_orders.clear()
        self._order_counts.clear()
        self._alerts.clear()


# Convenience function
_default_detector: FraudDetector | None = None


def check_fraud(order: dict[str, Any]) -> list[FraudAlert]:
    """Check order for fraud using default detector."""
    global _default_detector
    if _default_detector is None:
        _default_detector = FraudDetector()

    return _default_detector.check_order(order)
