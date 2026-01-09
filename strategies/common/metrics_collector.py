"""
MetricsCollector for NautilusTrader TradingNode

Emits trading metrics to QuestDB via ILP protocol.
Designed for real-time monitoring dashboards.

Usage:
    from strategies.common.metrics_collector import MetricsCollector

    # In TradingNode setup
    collector = MetricsCollector()

    # In strategy
    collector.emit_pnl(strategy_id, realized_pnl, unrealized_pnl)
    collector.emit_order_latency(strategy_id, instrument, latency_ms)
    collector.emit_position_change(strategy_id, instrument, quantity, side)
    collector.emit_error(strategy_id, error_type, message)
"""

import os
import socket
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class MetricsConfig:
    """Configuration for QuestDB connection."""

    host: str = "localhost"
    port: int = 9009
    enabled: bool = True

    @classmethod
    def from_env(cls) -> "MetricsConfig":
        """Load config from environment variables."""
        return cls(
            host=os.environ.get("QUESTDB_HOST", "localhost"),
            port=int(os.environ.get("QUESTDB_ILP_PORT", "9009")),
            enabled=os.environ.get("METRICS_ENABLED", "true").lower() == "true",
        )


class MetricsCollector:
    """
    Collects and emits trading metrics to QuestDB.

    Uses InfluxDB Line Protocol (ILP) over TCP for high-performance writes.
    """

    def __init__(self, config: MetricsConfig | None = None):
        self.config = config or MetricsConfig.from_env()
        self._socket: socket.socket | None = None
        self._connected = False

    def _connect(self) -> bool:
        """Establish connection to QuestDB."""
        if not self.config.enabled:
            return False

        if self._connected and self._socket:
            return True

        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.config.host, self.config.port))
            self._connected = True
            return True
        except (OSError, ConnectionRefusedError):
            self._connected = False
            return False

    def _send(self, line: str) -> bool:
        """Send ILP line to QuestDB."""
        if not self._connect():
            return False

        try:
            self._socket.sendall((line + "\n").encode())  # type: ignore[union-attr]
            return True
        except (OSError, BrokenPipeError):
            self._connected = False
            return False

    def _timestamp_ns(self) -> int:
        """Get current timestamp in nanoseconds."""
        return int(time.time() * 1_000_000_000)

    def _escape_tag(self, value: str) -> str:
        """Escape special characters in tag values."""
        return value.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")

    def _escape_field(self, value: Any) -> str:
        """Format field value for ILP."""
        if isinstance(value, bool):
            return "t" if value else "f"
        elif isinstance(value, int):
            return f"{value}i"
        elif isinstance(value, float):
            return str(value)
        elif isinstance(value, str):
            return f'"{value.replace(chr(34), chr(92) + chr(34))}"'
        return str(value)

    # =========================================================================
    # Metric Emission Methods
    # =========================================================================

    def emit_pnl(
        self,
        strategy_id: str,
        realized_pnl: float,
        unrealized_pnl: float,
        total_pnl: float | None = None,
    ) -> bool:
        """
        Emit PnL metrics.

        Args:
            strategy_id: Strategy identifier
            realized_pnl: Realized profit/loss
            unrealized_pnl: Unrealized profit/loss
            total_pnl: Total PnL (calculated if not provided)
        """
        if total_pnl is None:
            total_pnl = realized_pnl + unrealized_pnl

        line = (
            f"trading_pnl,strategy_id={self._escape_tag(strategy_id)} "
            f"realized={realized_pnl},unrealized={unrealized_pnl},total={total_pnl} "
            f"{self._timestamp_ns()}"
        )
        return self._send(line)

    def emit_order_latency(
        self,
        strategy_id: str,
        instrument_id: str,
        latency_ms: float,
        order_type: str = "market",
    ) -> bool:
        """
        Emit order execution latency.

        Args:
            strategy_id: Strategy identifier
            instrument_id: Instrument being traded
            latency_ms: Round-trip latency in milliseconds
            order_type: Type of order (market, limit, etc.)
        """
        line = (
            f"order_latency,strategy_id={self._escape_tag(strategy_id)},"
            f"instrument_id={self._escape_tag(instrument_id)},"
            f"order_type={self._escape_tag(order_type)} "
            f"latency_ms={latency_ms} "
            f"{self._timestamp_ns()}"
        )
        return self._send(line)

    def emit_position_change(
        self,
        strategy_id: str,
        instrument_id: str,
        quantity: float,
        side: str,
        avg_price: float | None = None,
        notional_value: float | None = None,
    ) -> bool:
        """
        Emit position change event.

        Args:
            strategy_id: Strategy identifier
            instrument_id: Instrument being traded
            quantity: Position quantity (absolute)
            side: Position side (LONG, SHORT, FLAT)
            avg_price: Average entry price
            notional_value: Notional value of position
        """
        fields = [f"quantity={quantity}"]
        if avg_price is not None:
            fields.append(f"avg_price={avg_price}")
        if notional_value is not None:
            fields.append(f"notional_value={notional_value}")

        line = (
            f"positions,strategy_id={self._escape_tag(strategy_id)},"
            f"instrument_id={self._escape_tag(instrument_id)},"
            f"side={self._escape_tag(side)} "
            f"{','.join(fields)} "
            f"{self._timestamp_ns()}"
        )
        return self._send(line)

    def emit_error(
        self,
        strategy_id: str,
        error_type: str,
        message: str,
        severity: str = "error",
    ) -> bool:
        """
        Emit error event.

        Args:
            strategy_id: Strategy identifier
            error_type: Type of error (connection, execution, validation, etc.)
            message: Error message
            severity: Severity level (warning, error, critical)
        """
        # Truncate message to prevent huge writes
        message = message[:500] if len(message) > 500 else message

        line = (
            f"error_events,strategy_id={self._escape_tag(strategy_id)},"
            f"error_type={self._escape_tag(error_type)},"
            f"severity={self._escape_tag(severity)} "
            f"error_message={self._escape_field(message)} "
            f"{self._timestamp_ns()}"
        )
        return self._send(line)

    def emit_risk_metrics(
        self,
        strategy_id: str,
        drawdown_pct: float,
        exposure_pct: float,
        leverage: float,
        daily_pnl: float,
    ) -> bool:
        """
        Emit risk metrics.

        Args:
            strategy_id: Strategy identifier
            drawdown_pct: Current drawdown percentage
            exposure_pct: Current exposure as percentage of account
            leverage: Current leverage
            daily_pnl: Daily profit/loss
        """
        line = (
            f"trading_risk,strategy_id={self._escape_tag(strategy_id)} "
            f"drawdown_pct={drawdown_pct},exposure_pct={exposure_pct},"
            f"leverage={leverage},daily_pnl={daily_pnl} "
            f"{self._timestamp_ns()}"
        )
        return self._send(line)

    def emit_health(
        self,
        component: str,
        status: str,
        latency_ms: float | None = None,
    ) -> bool:
        """
        Emit system health check.

        Args:
            component: Component name (exchange, database, etc.)
            status: Status (healthy, degraded, unhealthy)
            latency_ms: Optional latency measurement
        """
        fields = [f'status="{status}"']
        if latency_ms is not None:
            fields.append(f"latency_ms={latency_ms}")

        line = (
            f"system_health,component={self._escape_tag(component)} "
            f"{','.join(fields)} "
            f"{self._timestamp_ns()}"
        )
        return self._send(line)

    def close(self) -> None:
        """Close connection to QuestDB."""
        if self._socket:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None
            self._connected = False
