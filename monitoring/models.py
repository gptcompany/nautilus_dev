# monitoring.models - Pydantic models for QuestDB metrics
#
# T011: Create Pydantic models for all metrics

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DaemonMetrics(BaseModel):
    """Metrics from CCXT DaemonRunner (Spec 001).

    Table: daemon_metrics
    """

    timestamp: datetime = Field(..., description="UTC timestamp")
    host: str = Field(..., min_length=1, max_length=255, description="Hostname")
    env: Literal["prod", "staging", "dev"] = Field(..., description="Environment")
    fetch_count: int = Field(..., ge=0, description="Cumulative OI/Funding fetches")
    error_count: int = Field(..., ge=0, description="Cumulative errors")
    liquidation_count: int = Field(..., ge=0, description="Cumulative liquidations")
    uptime_seconds: float = Field(..., ge=0, description="Time since daemon start")
    running: bool = Field(..., description="Daemon running state")
    last_error: str | None = Field(default=None, description="Last error message")

    def to_ilp_line(self) -> str:
        """Convert to InfluxDB Line Protocol format for QuestDB HTTP ILP."""
        # Tags (dimensions)
        tags = f"host={self.host},env={self.env}"

        # Fields
        fields = [
            f"fetch_count={self.fetch_count}i",
            f"error_count={self.error_count}i",
            f"liquidation_count={self.liquidation_count}i",
            f"uptime_seconds={self.uptime_seconds}",
            f"running={'t' if self.running else 'f'}",
        ]
        if self.last_error:
            # Escape special chars in string field for ILP format
            # Order matters: backslashes first, then quotes, then control chars
            escaped = (
                self.last_error.replace("\\", "\\\\")
                .replace('"', '\\"')
                .replace("\n", "\\n")
                .replace("\r", "\\r")
                .replace("\t", "\\t")
            )
            fields.append(f'last_error="{escaped}"')

        fields_str = ",".join(fields)

        # Timestamp in nanoseconds
        ts_ns = int(self.timestamp.timestamp() * 1_000_000_000)

        return f"daemon_metrics,{tags} {fields_str} {ts_ns}"


class ExchangeStatus(BaseModel):
    """Connectivity status per exchange.

    Table: exchange_status
    """

    timestamp: datetime = Field(..., description="UTC timestamp")
    exchange: Literal["binance", "bybit", "okx", "dydx"] = Field(..., description="Exchange")
    host: str = Field(..., min_length=1, max_length=255, description="Hostname")
    env: Literal["prod", "staging", "dev"] = Field(..., description="Environment")
    connected: bool = Field(..., description="WebSocket connected")
    latency_ms: float = Field(..., ge=0, le=10000, description="Round-trip latency ms")
    reconnect_count: int = Field(..., ge=0, description="Cumulative reconnections")
    last_message_at: datetime | None = Field(default=None, description="Last message received")
    disconnected_at: datetime | None = Field(default=None, description="Last disconnect time")

    def to_ilp_line(self) -> str:
        """Convert to InfluxDB Line Protocol format."""
        tags = f"exchange={self.exchange},host={self.host},env={self.env}"

        fields = [
            f"connected={'t' if self.connected else 'f'}",
            f"latency_ms={self.latency_ms}",
            f"reconnect_count={self.reconnect_count}i",
        ]
        if self.last_message_at:
            ts_ns = int(self.last_message_at.timestamp() * 1_000_000_000)
            fields.append(f"last_message_at={ts_ns}i")
        if self.disconnected_at:
            ts_ns = int(self.disconnected_at.timestamp() * 1_000_000_000)
            fields.append(f"disconnected_at={ts_ns}i")

        fields_str = ",".join(fields)
        ts_ns = int(self.timestamp.timestamp() * 1_000_000_000)

        return f"exchange_status,{tags} {fields_str} {ts_ns}"


class PipelineMetrics(BaseModel):
    """Data pipeline throughput metrics.

    Table: pipeline_metrics
    """

    timestamp: datetime = Field(..., description="UTC timestamp")
    exchange: Literal["binance", "bybit", "okx", "dydx"] = Field(..., description="Exchange")
    symbol: str = Field(..., min_length=1, description="Symbol e.g. BTC/USDT:USDT")
    data_type: Literal["oi", "funding", "liquidation"] = Field(..., description="Data type")
    host: str = Field(..., min_length=1, max_length=255, description="Hostname")
    env: Literal["prod", "staging", "dev"] = Field(..., description="Environment")
    records_count: int = Field(..., ge=0, description="Records in interval")
    bytes_written: int = Field(..., ge=0, description="Bytes written to storage")
    latency_ms: float = Field(..., ge=0, description="Processing latency ms")
    gap_detected: bool = Field(default=False, description="Data gap detected")
    gap_duration_seconds: float | None = Field(default=None, description="Gap duration")

    def to_ilp_line(self) -> str:
        """Convert to InfluxDB Line Protocol format."""
        # Escape special chars in symbol for tags
        escaped_symbol = self.symbol.replace(" ", "\\ ").replace(",", "\\,")
        tags = f"exchange={self.exchange},symbol={escaped_symbol},data_type={self.data_type},host={self.host},env={self.env}"

        fields = [
            f"records_count={self.records_count}i",
            f"bytes_written={self.bytes_written}i",
            f"latency_ms={self.latency_ms}",
            f"gap_detected={'t' if self.gap_detected else 'f'}",
        ]
        if self.gap_duration_seconds is not None:
            fields.append(f"gap_duration_seconds={self.gap_duration_seconds}")

        fields_str = ",".join(fields)
        ts_ns = int(self.timestamp.timestamp() * 1_000_000_000)

        return f"pipeline_metrics,{tags} {fields_str} {ts_ns}"


class EvolutionMetrics(BaseModel):
    """Evolution metrics for Alpha-Evolve Grafana dashboard.

    Table: evolution_metrics
    Spec: 010-alpha-evolve-dashboard
    """

    timestamp: datetime = Field(..., description="UTC timestamp")
    program_id: str = Field(..., min_length=1, description="Strategy UUID")
    experiment: str = Field(..., min_length=1, description="Experiment name")
    generation: int = Field(..., ge=0, description="Generation number (0 = seed)")
    parent_id: str | None = Field(default=None, description="Parent strategy UUID")

    # Fitness metrics
    sharpe: float = Field(..., description="Sharpe ratio")
    calmar: float = Field(..., description="Calmar ratio (primary fitness)")
    max_dd: float = Field(..., ge=0, le=100, description="Maximum drawdown %")
    cagr: float = Field(..., description="Compound annual growth rate")
    total_return: float = Field(..., description="Total return percentage")
    trade_count: int | None = Field(default=None, ge=0, description="Trades executed")
    win_rate: float | None = Field(default=None, ge=0, le=1, description="Win rate 0-1")
    # MVP enhancements (2026-01-11)
    psr: float | None = Field(default=None, ge=0, le=1, description="Probabilistic Sharpe Ratio")
    net_sharpe: float | None = Field(default=None, description="Transaction cost-adjusted Sharpe")

    # Mutation tracking
    mutation_outcome: Literal["success", "syntax_error", "runtime_error", "timeout", "seed"] = (
        Field(..., description="Mutation result category")
    )
    mutation_latency_ms: float = Field(default=0.0, ge=0, description="Mutation API latency")

    def to_ilp_line(self) -> str:
        """Convert to InfluxDB Line Protocol format for QuestDB HTTP ILP."""
        # Tags (dimensions) - escape special chars (space, comma, equals)
        # Order: space, comma, equals (ILP protocol requirement)
        escaped_program_id = (
            self.program_id.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")
        )
        escaped_experiment = (
            self.experiment.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")
        )
        tags = f"program_id={escaped_program_id},experiment={escaped_experiment},mutation_outcome={self.mutation_outcome}"

        # Fields
        fields = [
            f"generation={self.generation}i",
            f"sharpe={self.sharpe}",
            f"calmar={self.calmar}",
            f"max_dd={self.max_dd}",
            f"cagr={self.cagr}",
            f"total_return={self.total_return}",
            f"mutation_latency_ms={self.mutation_latency_ms}",
        ]

        if self.parent_id:
            escaped_parent = self.parent_id.replace("\\", "\\\\").replace('"', '\\"')
            fields.append(f'parent_id="{escaped_parent}"')

        if self.trade_count is not None:
            fields.append(f"trade_count={self.trade_count}i")

        if self.win_rate is not None:
            fields.append(f"win_rate={self.win_rate}")

        # MVP fields (2026-01-11)
        if self.psr is not None:
            fields.append(f"psr={self.psr}")

        if self.net_sharpe is not None:
            fields.append(f"net_sharpe={self.net_sharpe}")

        fields_str = ",".join(fields)

        # Timestamp in nanoseconds
        ts_ns = int(self.timestamp.timestamp() * 1_000_000_000)

        return f"evolution_metrics,{tags} {fields_str} {ts_ns}"


class TradingMetrics(BaseModel):
    """Real-time trading performance metrics.

    Table: trading_metrics
    """

    timestamp: datetime = Field(..., description="UTC timestamp")
    strategy: str = Field(..., min_length=1, description="Strategy identifier")
    symbol: str = Field(..., min_length=1, description="Trading symbol")
    venue: Literal["binance", "bybit", "okx", "dydx"] = Field(..., description="Venue")
    env: Literal["prod", "staging", "dev"] = Field(..., description="Environment")
    pnl: float = Field(..., description="Realized PnL")
    unrealized_pnl: float = Field(..., description="Unrealized PnL")
    position_size: float = Field(..., description="Current position size")
    orders_placed: int = Field(default=0, ge=0, description="Orders placed")
    orders_filled: int = Field(default=0, ge=0, description="Orders filled")
    fill_rate: float = Field(default=0.0, ge=0, le=1, description="Fill rate")
    exposure: float = Field(default=0.0, description="Total exposure")
    drawdown: float = Field(default=0.0, ge=0, description="Current drawdown %")

    def to_ilp_line(self) -> str:
        """Convert to InfluxDB Line Protocol format."""
        escaped_strategy = self.strategy.replace(" ", "\\ ").replace(",", "\\,")
        escaped_symbol = self.symbol.replace(" ", "\\ ").replace(",", "\\,")
        tags = (
            f"strategy={escaped_strategy},symbol={escaped_symbol},venue={self.venue},env={self.env}"
        )

        fields = [
            f"pnl={self.pnl}",
            f"unrealized_pnl={self.unrealized_pnl}",
            f"position_size={self.position_size}",
            f"orders_placed={self.orders_placed}i",
            f"orders_filled={self.orders_filled}i",
            f"fill_rate={self.fill_rate}",
            f"exposure={self.exposure}",
            f"drawdown={self.drawdown}",
        ]

        fields_str = ",".join(fields)
        ts_ns = int(self.timestamp.timestamp() * 1_000_000_000)

        return f"trading_metrics,{tags} {fields_str} {ts_ns}"


class CircuitBreakerMetrics(BaseModel):
    """Circuit breaker state metrics.

    Table: circuit_breaker_state
    Spec: 012-circuit-breaker-drawdown
    """

    timestamp: datetime = Field(..., description="UTC timestamp")
    trader_id: str = Field(..., min_length=1, description="Trader identifier")
    state: Literal["active", "warning", "reducing", "halted"] = Field(
        ..., description="Circuit breaker state"
    )
    current_drawdown: float = Field(..., ge=0, description="Current drawdown as decimal")
    peak_equity: float = Field(..., ge=0, description="High water mark")
    current_equity: float = Field(..., description="Current equity value")
    env: Literal["prod", "staging", "dev"] = Field(..., description="Environment")

    def to_ilp_line(self) -> str:
        """Convert to InfluxDB Line Protocol format for QuestDB HTTP ILP."""
        # Tags (dimensions)
        escaped_trader_id = (
            self.trader_id.replace(" ", "\\ ").replace(",", "\\,").replace("=", "\\=")
        )
        tags = f"trader_id={escaped_trader_id},state={self.state},env={self.env}"

        # Fields
        fields = [
            f"current_drawdown={self.current_drawdown}",
            f"peak_equity={self.peak_equity}",
            f"current_equity={self.current_equity}",
        ]

        fields_str = ",".join(fields)

        # Timestamp in nanoseconds
        ts_ns = int(self.timestamp.timestamp() * 1_000_000_000)

        return f"circuit_breaker_state,{tags} {fields_str} {ts_ns}"


__all__ = [
    "CircuitBreakerMetrics",
    "DaemonMetrics",
    "EvolutionMetrics",
    "ExchangeStatus",
    "PipelineMetrics",
    "TradingMetrics",
]
