"""Tests for pipeline stage implementations."""

import pytest

from pipeline.core.state import PipelineState
from pipeline.core.types import (
    Confidence,
    PipelineStatus,
    StageResult,
    StageType,
)
from pipeline.stages.alpha import AlphaConfig, AlphaStage
from pipeline.stages.base import AbstractStage
from pipeline.stages.data import DataConfig, DataStage
from pipeline.stages.monitoring import MonitoringConfig, MonitoringStage
from pipeline.stages.risk import RiskConfig, RiskStage


class TestDataStage:
    """Test DataStage implementation."""

    def test_stage_type(self):
        """Test stage type is DATA."""
        stage = DataStage()
        assert stage.stage_type == StageType.DATA

    def test_no_dependencies(self):
        """Test data stage has no dependencies."""
        stage = DataStage()
        assert stage.get_dependencies() == []

    def test_validate_input_with_data_path(self):
        """Test validation passes with data_path."""
        stage = DataStage()
        state = PipelineState.create(config={"data_path": "./data/test.parquet"})
        assert stage.validate_input(state) is True

    def test_validate_input_with_catalog_path(self):
        """Test validation passes with catalog_path."""
        stage = DataStage()
        state = PipelineState.create(config={"catalog_path": "./catalog"})
        assert stage.validate_input(state) is True

    def test_validate_input_empty_config(self):
        """Test validation fails with empty config."""
        stage = DataStage()
        state = PipelineState.create(config={})
        assert stage.validate_input(state) is False

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        stage = DataStage()
        state = PipelineState.create(
            config={
                "data_path": "./data/test.parquet",
                "min_records": 10,
            }
        )
        result = await stage.execute(state)
        assert result.stage == StageType.DATA
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None

    def test_parse_config(self):
        """Test config parsing."""
        stage = DataStage()
        config = stage._parse_config(
            {
                "data_path": "./data",
                "min_records": 500,
                "symbols": ["BTCUSDT"],
            }
        )
        assert config.data_path == "./data"
        assert config.min_records == 500
        assert "BTCUSDT" in config.symbols


class TestAlphaStage:
    """Test AlphaStage implementation."""

    def test_stage_type(self):
        """Test stage type is ALPHA."""
        stage = AlphaStage()
        assert stage.stage_type == StageType.ALPHA

    def test_depends_on_data(self):
        """Test alpha depends on DATA stage."""
        stage = AlphaStage()
        assert StageType.DATA in stage.get_dependencies()

    def test_validate_input_missing_data(self):
        """Test validation fails without DATA result."""
        stage = AlphaStage()
        state = PipelineState.create(config={})
        assert stage.validate_input(state) is False

    def test_validate_input_with_data_result(self):
        """Test validation passes with DATA result."""
        stage = AlphaStage()
        state = PipelineState.create(config={})
        state.stage_results[StageType.DATA] = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={"source": "test", "record_count": 1000},
        )
        assert stage.validate_input(state) is True

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        stage = AlphaStage()
        state = PipelineState.create(
            config={
                "model_type": "momentum",
                "min_sharpe": 0.5,
            }
        )
        state.stage_results[StageType.DATA] = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={"source": "test", "record_count": 1000},
        )
        result = await stage.execute(state)
        assert result.stage == StageType.ALPHA
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
        assert "alpha" in result.output
        assert "metrics" in result.output

    def test_parse_config(self):
        """Test config parsing."""
        stage = AlphaStage()
        config = stage._parse_config(
            {
                "model_type": "mean_reversion",
                "min_sharpe": 1.5,
                "max_overfitting": 0.2,
            }
        )
        assert config.model_type == "mean_reversion"
        assert config.min_sharpe == 1.5
        assert config.max_overfitting == 0.2


class TestRiskStage:
    """Test RiskStage implementation."""

    def test_stage_type(self):
        """Test stage type is RISK."""
        stage = RiskStage()
        assert stage.stage_type == StageType.RISK

    def test_depends_on_alpha(self):
        """Test risk depends on ALPHA stage."""
        stage = RiskStage()
        assert StageType.ALPHA in stage.get_dependencies()

    def test_requires_high_confidence(self):
        """Test risk requires HIGH confidence."""
        stage = RiskStage()
        assert stage.get_confidence_requirement() == Confidence.HIGH_CONFIDENCE

    def test_validate_input_missing_alpha(self):
        """Test validation fails without ALPHA result."""
        stage = RiskStage()
        state = PipelineState.create(config={})
        assert stage.validate_input(state) is False

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        stage = RiskStage()
        state = PipelineState.create(
            config={
                "max_leverage": 2.0,
                "stop_loss_pct": 3.0,
            }
        )
        state.stage_results[StageType.ALPHA] = StageResult(
            stage=StageType.ALPHA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={
                "alpha": {"model_type": "test"},
                "metrics": {"sharpe_ratio": 1.0, "max_drawdown": 0.1},
            },
        )
        result = await stage.execute(state)
        assert result.stage == StageType.RISK
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
        assert "risk_metrics" in result.output
        assert "positions" in result.output

    def test_parse_config_defaults(self):
        """Test config parsing with defaults."""
        stage = RiskStage()
        config = stage._parse_config({})
        # Check FIXED safety limits (per CLAUDE.md)
        assert config.max_leverage == 3.0
        assert config.max_position_pct == 10.0
        assert config.stop_loss_pct == 5.0
        assert config.daily_loss_limit_pct == 2.0
        assert config.kill_switch_drawdown == 15.0


class TestMonitoringStage:
    """Test MonitoringStage implementation."""

    def test_stage_type(self):
        """Test stage type is MONITORING."""
        stage = MonitoringStage()
        assert stage.stage_type == StageType.MONITORING

    def test_no_required_dependencies(self):
        """Test monitoring has no required dependencies."""
        stage = MonitoringStage()
        assert stage.get_dependencies() == []

    def test_validate_input_always_true(self):
        """Test validation always passes."""
        stage = MonitoringStage()
        state = PipelineState.create(config={})
        assert stage.validate_input(state) is True

    @pytest.mark.asyncio
    async def test_execute_success(self):
        """Test successful execution."""
        stage = MonitoringStage()
        state = PipelineState.create(
            config={
                "alert_drawdown_pct": 5.0,
                "enable_console": True,
            }
        )
        result = await stage.execute(state)
        assert result.stage == StageType.MONITORING
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
        assert "metrics" in result.output
        assert "alerts" in result.output

    @pytest.mark.asyncio
    async def test_execute_with_risk_context(self):
        """Test execution with risk stage context."""
        stage = MonitoringStage()
        state = PipelineState.create(config={})
        state.stage_results[StageType.RISK] = StageResult(
            stage=StageType.RISK,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={
                "risk_metrics": {"var_pct": 3.0, "leverage_used": 1.5},
                "positions": [],
            },
        )
        result = await stage.execute(state)
        assert result.output.get("risk_context") is not None

    def test_parse_config(self):
        """Test config parsing."""
        stage = MonitoringStage()
        config = stage._parse_config(
            {
                "alert_drawdown_pct": 8.0,
                "discord_webhook": "https://discord.com/webhook",
            }
        )
        assert config.alert_drawdown_pct == 8.0
        assert config.discord_webhook == "https://discord.com/webhook"


class TestAbstractStage:
    """Test AbstractStage base class."""

    def test_cannot_instantiate_abstract(self):
        """Test abstract class cannot be instantiated."""
        with pytest.raises(TypeError):
            AbstractStage()  # type: ignore

    def test_default_confidence_requirement(self):
        """Test default confidence requirement is MEDIUM."""

        class TestStage(AbstractStage):
            @property
            def stage_type(self) -> StageType:
                return StageType.DATA

            async def execute(self, state: PipelineState) -> StageResult:
                return StageResult(
                    stage=self.stage_type,
                    status=PipelineStatus.COMPLETED,
                    confidence=Confidence.HIGH_CONFIDENCE,
                    output=None,
                )

            def validate_input(self, state: PipelineState) -> bool:
                return True

        stage = TestStage()
        assert stage.get_confidence_requirement() == Confidence.MEDIUM_CONFIDENCE

    def test_default_dependencies_empty(self):
        """Test default dependencies is empty."""

        class TestStage(AbstractStage):
            @property
            def stage_type(self) -> StageType:
                return StageType.DATA

            async def execute(self, state: PipelineState) -> StageResult:
                return StageResult(
                    stage=self.stage_type,
                    status=PipelineStatus.COMPLETED,
                    confidence=Confidence.HIGH_CONFIDENCE,
                    output=None,
                )

            def validate_input(self, state: PipelineState) -> bool:
                return True

        stage = TestStage()
        assert stage.get_dependencies() == []


class TestDataConfig:
    """Test DataConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = DataConfig()
        assert config.data_path is None
        assert config.min_records == 100
        assert config.validate_quality is True


class TestAlphaConfig:
    """Test AlphaConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = AlphaConfig()
        assert config.model_type == "default"
        assert config.min_sharpe == 0.5
        assert config.max_overfitting == 0.3


class TestRiskConfig:
    """Test RiskConfig dataclass."""

    def test_fixed_safety_limits(self):
        """Test safety limits match CLAUDE.md requirements."""
        config = RiskConfig()
        # These are FIXED per CLAUDE.md - Knight Capital lost $440M
        assert config.max_leverage == 3.0
        assert config.max_position_pct == 10.0
        assert config.stop_loss_pct == 5.0
        assert config.daily_loss_limit_pct == 2.0
        assert config.kill_switch_drawdown == 15.0


class TestMonitoringConfig:
    """Test MonitoringConfig dataclass."""

    def test_defaults(self):
        """Test default values."""
        config = MonitoringConfig()
        assert "pnl" in config.metrics
        assert "drawdown" in config.metrics
        assert config.enable_console is True
        assert config.dashboard_enabled is True
