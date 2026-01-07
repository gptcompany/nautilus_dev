# TDD RED Phase: Tests for monitoring models (T007-T009)
# These tests MUST fail initially until models.py is implemented

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError


class TestDaemonMetrics:
    """Tests for DaemonMetrics model validation (T007)."""

    def test_valid_daemon_metrics_creates_successfully(self):
        """Valid metrics should create without errors."""
        from monitoring.models import DaemonMetrics

        metrics = DaemonMetrics(
            timestamp=datetime.now(UTC),
            host="prod-server-01",
            env="prod",
            fetch_count=100,
            error_count=5,
            liquidation_count=50,
            uptime_seconds=3600.0,
            running=True,
        )
        assert metrics.host == "prod-server-01"
        assert metrics.running is True

    def test_daemon_metrics_env_must_be_valid(self):
        """env must be one of: prod, staging, dev."""
        from monitoring.models import DaemonMetrics

        with pytest.raises(ValidationError):
            DaemonMetrics(
                timestamp=datetime.now(UTC),
                host="server",
                env="invalid_env",  # Invalid
                fetch_count=0,
                error_count=0,
                liquidation_count=0,
                uptime_seconds=0.0,
                running=True,
            )

    def test_daemon_metrics_counters_must_be_non_negative(self):
        """Counters (fetch_count, error_count) must be >= 0."""
        from monitoring.models import DaemonMetrics

        with pytest.raises(ValidationError):
            DaemonMetrics(
                timestamp=datetime.now(UTC),
                host="server",
                env="prod",
                fetch_count=-1,  # Invalid
                error_count=0,
                liquidation_count=0,
                uptime_seconds=0.0,
                running=True,
            )

    def test_daemon_metrics_uptime_must_be_non_negative(self):
        """uptime_seconds must be >= 0."""
        from monitoring.models import DaemonMetrics

        with pytest.raises(ValidationError):
            DaemonMetrics(
                timestamp=datetime.now(UTC),
                host="server",
                env="prod",
                fetch_count=0,
                error_count=0,
                liquidation_count=0,
                uptime_seconds=-100.0,  # Invalid
                running=True,
            )

    def test_daemon_metrics_host_must_be_non_empty(self):
        """host must be non-empty string."""
        from monitoring.models import DaemonMetrics

        with pytest.raises(ValidationError):
            DaemonMetrics(
                timestamp=datetime.now(UTC),
                host="",  # Invalid
                env="prod",
                fetch_count=0,
                error_count=0,
                liquidation_count=0,
                uptime_seconds=0.0,
                running=True,
            )

    def test_daemon_metrics_last_error_optional(self):
        """last_error should be optional (None by default)."""
        from monitoring.models import DaemonMetrics

        metrics = DaemonMetrics(
            timestamp=datetime.now(UTC),
            host="server",
            env="prod",
            fetch_count=0,
            error_count=0,
            liquidation_count=0,
            uptime_seconds=0.0,
            running=True,
        )
        assert metrics.last_error is None

    def test_daemon_metrics_to_ilp_line(self):
        """Model should convert to ILP line protocol format."""
        from monitoring.models import DaemonMetrics

        ts = datetime(2025, 12, 26, 12, 0, 0, tzinfo=UTC)
        metrics = DaemonMetrics(
            timestamp=ts,
            host="prod-01",
            env="prod",
            fetch_count=100,
            error_count=5,
            liquidation_count=50,
            uptime_seconds=3600.0,
            running=True,
        )
        line = metrics.to_ilp_line()
        assert "daemon_metrics" in line
        assert "host=prod-01" in line
        assert "fetch_count=100i" in line


class TestExchangeStatus:
    """Tests for ExchangeStatus model validation (T008)."""

    def test_valid_exchange_status_creates_successfully(self):
        """Valid status should create without errors."""
        from monitoring.models import ExchangeStatus

        status = ExchangeStatus(
            timestamp=datetime.now(UTC),
            exchange="binance",
            host="server",
            env="prod",
            connected=True,
            latency_ms=50.0,
            reconnect_count=0,
        )
        assert status.connected is True
        assert status.exchange == "binance"

    def test_exchange_status_exchange_must_be_valid(self):
        """exchange must be one of: binance, bybit, okx, dydx."""
        from monitoring.models import ExchangeStatus

        with pytest.raises(ValidationError):
            ExchangeStatus(
                timestamp=datetime.now(UTC),
                exchange="invalid_exchange",  # Invalid
                host="server",
                env="prod",
                connected=True,
                latency_ms=50.0,
                reconnect_count=0,
            )

    def test_exchange_status_latency_must_be_non_negative(self):
        """latency_ms must be >= 0."""
        from monitoring.models import ExchangeStatus

        with pytest.raises(ValidationError):
            ExchangeStatus(
                timestamp=datetime.now(UTC),
                exchange="binance",
                host="server",
                env="prod",
                connected=True,
                latency_ms=-10.0,  # Invalid
                reconnect_count=0,
            )

    def test_exchange_status_latency_reasonable_upper_bound(self):
        """latency_ms should have reasonable upper bound (10000ms)."""
        from monitoring.models import ExchangeStatus

        with pytest.raises(ValidationError):
            ExchangeStatus(
                timestamp=datetime.now(UTC),
                exchange="binance",
                host="server",
                env="prod",
                connected=True,
                latency_ms=15000.0,  # Too high
                reconnect_count=0,
            )

    def test_exchange_status_optional_timestamps(self):
        """last_message_at and disconnected_at should be optional."""
        from monitoring.models import ExchangeStatus

        status = ExchangeStatus(
            timestamp=datetime.now(UTC),
            exchange="bybit",
            host="server",
            env="prod",
            connected=True,
            latency_ms=50.0,
            reconnect_count=0,
        )
        assert status.last_message_at is None
        assert status.disconnected_at is None

    def test_exchange_status_to_ilp_line(self):
        """Model should convert to ILP line protocol format."""
        from monitoring.models import ExchangeStatus

        ts = datetime(2025, 12, 26, 12, 0, 0, tzinfo=UTC)
        status = ExchangeStatus(
            timestamp=ts,
            exchange="binance",
            host="server",
            env="prod",
            connected=True,
            latency_ms=50.5,
            reconnect_count=3,
        )
        line = status.to_ilp_line()
        assert "exchange_status" in line
        assert "exchange=binance" in line
        assert "connected=t" in line or "connected=T" in line


class TestPipelineMetrics:
    """Tests for PipelineMetrics model validation (T009)."""

    def test_valid_pipeline_metrics_creates_successfully(self):
        """Valid metrics should create without errors."""
        from monitoring.models import PipelineMetrics

        metrics = PipelineMetrics(
            timestamp=datetime.now(UTC),
            exchange="binance",
            symbol="BTC/USDT:USDT",
            data_type="oi",
            host="server",
            env="prod",
            records_count=1000,
            bytes_written=50000,
            latency_ms=25.0,
        )
        assert metrics.data_type == "oi"
        assert metrics.records_count == 1000

    def test_pipeline_metrics_data_type_must_be_valid(self):
        """data_type must be one of: oi, funding, liquidation."""
        from monitoring.models import PipelineMetrics

        with pytest.raises(ValidationError):
            PipelineMetrics(
                timestamp=datetime.now(UTC),
                exchange="binance",
                symbol="BTC/USDT:USDT",
                data_type="invalid_type",  # Invalid
                host="server",
                env="prod",
                records_count=0,
                bytes_written=0,
                latency_ms=0.0,
            )

    def test_pipeline_metrics_counts_must_be_non_negative(self):
        """records_count and bytes_written must be >= 0."""
        from monitoring.models import PipelineMetrics

        with pytest.raises(ValidationError):
            PipelineMetrics(
                timestamp=datetime.now(UTC),
                exchange="binance",
                symbol="BTC/USDT:USDT",
                data_type="oi",
                host="server",
                env="prod",
                records_count=-1,  # Invalid
                bytes_written=0,
                latency_ms=0.0,
            )

    def test_pipeline_metrics_gap_detected_logic(self):
        """gap_duration_seconds only valid when gap_detected is True."""
        from monitoring.models import PipelineMetrics

        # Valid: gap_detected=True with duration
        metrics = PipelineMetrics(
            timestamp=datetime.now(UTC),
            exchange="binance",
            symbol="BTC/USDT:USDT",
            data_type="oi",
            host="server",
            env="prod",
            records_count=0,
            bytes_written=0,
            latency_ms=0.0,
            gap_detected=True,
            gap_duration_seconds=120.0,
        )
        assert metrics.gap_duration_seconds == 120.0

    def test_pipeline_metrics_to_ilp_line(self):
        """Model should convert to ILP line protocol format."""
        from monitoring.models import PipelineMetrics

        ts = datetime(2025, 12, 26, 12, 0, 0, tzinfo=UTC)
        metrics = PipelineMetrics(
            timestamp=ts,
            exchange="binance",
            symbol="BTC/USDT:USDT",
            data_type="funding",
            host="server",
            env="prod",
            records_count=500,
            bytes_written=25000,
            latency_ms=10.5,
        )
        line = metrics.to_ilp_line()
        assert "pipeline_metrics" in line
        assert "data_type=funding" in line
        assert "records_count=500i" in line
