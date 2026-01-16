"""
Metrics Collector for NautilusTrader
Sends trading metrics to QuestDB for monitoring and alerting.

Usage:
    collector = MetricsCollector(questdb_host="localhost", questdb_port=9009)
    collector.record_pnl(strategy_id="STRAT-001", symbol="BTCUSDT", realized=100.0)
    collector.flush()  # Or auto-flushes every N records
"""

import logging
import socket
import time
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MetricsCollector:
    """Collects and sends metrics to QuestDB via ILP (InfluxDB Line Protocol)."""

    questdb_host: str = "localhost"
    questdb_port: int = 9009  # ILP port
    buffer_size: int = 100
    auto_flush: bool = True

    _buffer: list[str] = field(default_factory=list, init=False)
    _socket: socket.socket | None = field(default=None, init=False)
    _connected: bool = field(default=False, init=False)

    def __post_init__(self):
        self._connect()

    def _connect(self) -> bool:
        """Connect to QuestDB ILP endpoint."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.connect((self.questdb_host, self.questdb_port))
            self._connected = True
            logger.info(f"Connected to QuestDB at {self.questdb_host}:{self.questdb_port}")
            return True
        except Exception as e:
            logger.warning(f"Failed to connect to QuestDB: {e}")
            self._connected = False
            return False

    def _send(self, line: str) -> bool:
        """Send a single line to QuestDB."""
        if not self._connected:
            if not self._connect():
                return False

        try:
            if self._socket is not None:
                self._socket.sendall((line + "\n").encode())
            return True
        except Exception as e:
            logger.error(f"Failed to send metric: {e}")
            self._connected = False
            return False

    def _format_line(
        self,
        measurement: str,
        tags: dict[str, str],
        fields: dict[str, Any],
        timestamp_ns: int | None = None,
    ) -> str:
        """Format as InfluxDB Line Protocol."""
        # Measurement and tags
        tag_str = ",".join(f"{k}={v}" for k, v in tags.items() if v)
        line = f"{measurement},{tag_str}" if tag_str else measurement

        # Fields
        field_parts = []
        for k, v in fields.items():
            if v is None:
                continue
            if isinstance(v, bool):
                field_parts.append(f"{k}={'t' if v else 'f'}")
            elif isinstance(v, int):
                field_parts.append(f"{k}={v}i")
            elif isinstance(v, float):
                field_parts.append(f"{k}={v}")
            elif isinstance(v, str):
                field_parts.append(f'{k}="{v}"')

        line += " " + ",".join(field_parts)

        # Timestamp (nanoseconds)
        if timestamp_ns is None:
            timestamp_ns = int(time.time() * 1_000_000_000)
        line += f" {timestamp_ns}"

        return line

    def _buffer_or_send(self, line: str):
        """Buffer the line or send immediately."""
        self._buffer.append(line)
        if self.auto_flush and len(self._buffer) >= self.buffer_size:
            self.flush()

    def flush(self) -> int:
        """Flush all buffered metrics to QuestDB."""
        if not self._buffer:
            return 0

        sent = 0
        for line in self._buffer:
            if self._send(line):
                sent += 1

        self._buffer.clear()
        return sent

    # =========================================================================
    # PnL Metrics
    # =========================================================================
    def record_pnl(
        self,
        strategy_id: str,
        symbol: str,
        realized_pnl: float = 0.0,
        unrealized_pnl: float = 0.0,
        cumulative_pnl: float = 0.0,
        trade_count: int = 0,
        win_count: int = 0,
        loss_count: int = 0,
    ):
        """Record PnL metrics."""
        line = self._format_line(
            "trading_pnl",
            {"strategy_id": strategy_id, "symbol": symbol},
            {
                "realized_pnl": realized_pnl,
                "unrealized_pnl": unrealized_pnl,
                "total_pnl": realized_pnl + unrealized_pnl,
                "cumulative_pnl": cumulative_pnl,
                "trade_count": trade_count,
                "win_count": win_count,
                "loss_count": loss_count,
            },
        )
        self._buffer_or_send(line)

    # =========================================================================
    # Position Metrics
    # =========================================================================
    def record_position(
        self,
        strategy_id: str,
        symbol: str,
        side: str,
        quantity: float,
        avg_entry_price: float,
        current_price: float,
        margin_used: float = 0.0,
    ):
        """Record position metrics."""
        unrealized_pnl = (current_price - avg_entry_price) * quantity
        if side == "SHORT":
            unrealized_pnl = -unrealized_pnl

        line = self._format_line(
            "trading_positions",
            {"strategy_id": strategy_id, "symbol": symbol, "side": side},
            {
                "quantity": quantity,
                "avg_entry_price": avg_entry_price,
                "current_price": current_price,
                "unrealized_pnl": unrealized_pnl,
                "margin_used": margin_used,
            },
        )
        self._buffer_or_send(line)

    # =========================================================================
    # Order Metrics
    # =========================================================================
    def record_order(
        self,
        strategy_id: str,
        symbol: str,
        order_id: str,
        order_type: str,
        side: str,
        quantity: float,
        price: float,
        filled_quantity: float,
        avg_fill_price: float,
        latency_ms: float,
        status: str,
    ):
        """Record order execution metrics."""
        slippage_bps = 0.0
        if price > 0 and avg_fill_price > 0:
            slippage_bps = abs(avg_fill_price - price) / price * 10000

        line = self._format_line(
            "trading_orders",
            {
                "strategy_id": strategy_id,
                "symbol": symbol,
                "order_type": order_type,
                "side": side,
                "status": status,
            },
            {
                "order_id": order_id,
                "quantity": quantity,
                "price": price,
                "filled_quantity": filled_quantity,
                "avg_fill_price": avg_fill_price,
                "slippage_bps": slippage_bps,
                "latency_ms": latency_ms,
            },
        )
        self._buffer_or_send(line)

    # =========================================================================
    # Risk Metrics
    # =========================================================================
    def record_risk(
        self,
        strategy_id: str,
        drawdown_pct: float,
        daily_pnl_pct: float,
        position_exposure_pct: float,
        leverage_used: float,
        margin_ratio: float = 1.0,
    ):
        """Record risk metrics."""
        # Calculate risk score (0-100)
        risk_score = min(
            100,
            max(
                0,
                drawdown_pct * 3  # Drawdown weighted heavily
                + abs(daily_pnl_pct) * 2  # Daily swings
                + position_exposure_pct  # Exposure
                + leverage_used * 10,  # Leverage
            ),
        )

        # Determine alert level
        if drawdown_pct > 10 or risk_score > 70:
            alert_level = "CRITICAL"
        elif drawdown_pct > 5 or risk_score > 50:
            alert_level = "WARNING"
        else:
            alert_level = "NORMAL"

        line = self._format_line(
            "trading_risk",
            {"strategy_id": strategy_id, "alert_level": alert_level},
            {
                "drawdown_pct": drawdown_pct,
                "daily_pnl_pct": daily_pnl_pct,
                "position_exposure_pct": position_exposure_pct,
                "leverage_used": leverage_used,
                "margin_ratio": margin_ratio,
                "risk_score": risk_score,
            },
        )
        self._buffer_or_send(line)

    # =========================================================================
    # System Health
    # =========================================================================
    def record_health(
        self,
        component: str,
        status: str,
        latency_ms: float = 0.0,
        error_count: int = 0,
        memory_mb: float = 0.0,
        cpu_pct: float = 0.0,
    ):
        """Record system health metrics."""
        line = self._format_line(
            "system_health",
            {"component": component, "status": status},
            {
                "latency_ms": latency_ms,
                "error_count": error_count,
                "memory_mb": memory_mb,
                "cpu_pct": cpu_pct,
            },
        )
        self._buffer_or_send(line)

    # =========================================================================
    # Error Events
    # =========================================================================
    def record_error(
        self,
        severity: str,
        component: str,
        message: str,
        strategy_id: str = "",
        error_code: str = "",
    ):
        """Record error event."""
        line = self._format_line(
            "error_events",
            {
                "severity": severity,
                "component": component,
                "strategy_id": strategy_id,
            },
            {
                "error_code": error_code,
                "message": message,
            },
        )
        self._buffer_or_send(line)

    def close(self):
        """Flush and close connection."""
        self.flush()
        if self._socket:
            self._socket.close()
            self._connected = False
