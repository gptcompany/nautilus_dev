"""Integration tests for full pipeline execution."""

import tempfile
from pathlib import Path

import pytest

from pipeline.alpha.evolve.adapter import AlphaEvolveAdapter
from pipeline.core.loop import PipelineLoop
from pipeline.core.state import PipelineState
from pipeline.core.types import Confidence, PipelineStatus, StageType
from pipeline.hitl.approval import ApprovalGate, ApprovalResponse
from pipeline.stages.data import DataStage
from pipeline.stages.monitoring import MonitoringStage
from pipeline.stages.risk import RiskStage


class MockApprovalGate(ApprovalGate):
    """Mock approval gate that auto-approves."""

    def __init__(self, auto_approve: bool = True):
        super().__init__()
        self.auto_approve = auto_approve
        self.approval_requests: list = []

    async def request_approval(self, pipeline_id: str, result) -> ApprovalResponse:
        """Auto-approve or reject based on config."""
        self.approval_requests.append((pipeline_id, result))
        return ApprovalResponse(
            approved=self.auto_approve,
            action="approve" if self.auto_approve else "reject",
            reviewer="mock",
        )


class TestFullPipelineExecution:
    """Test full pipeline execution end-to-end."""

    @pytest.mark.asyncio
    async def test_minimal_pipeline_data_only(self):
        """Test pipeline with just data stage."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)

            stages = [DataStage()]
            approval_gate = MockApprovalGate(auto_approve=True)

            loop = PipelineLoop(
                stages=stages,
                approval_gate=approval_gate,
                checkpoint_dir=checkpoint_dir,
            )

            state = PipelineState.create(
                config={"data_path": "./test_data.parquet", "min_records": 1}
            )

            result_state = await loop.run(state)

            assert result_state.status == PipelineStatus.COMPLETED
            assert StageType.DATA in result_state.stage_results

    @pytest.mark.asyncio
    async def test_pipeline_data_alpha(self):
        """Test pipeline with data and alpha stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)

            stages = [DataStage(), AlphaEvolveAdapter()]
            approval_gate = MockApprovalGate(auto_approve=True)

            loop = PipelineLoop(
                stages=stages,
                approval_gate=approval_gate,
                checkpoint_dir=checkpoint_dir,
            )

            state = PipelineState.create(
                config={
                    "data_path": "./test_data.parquet",
                    "min_records": 1,
                    "evolution_generations": 5,
                }
            )

            result_state = await loop.run(state)

            assert result_state.status == PipelineStatus.COMPLETED
            assert StageType.DATA in result_state.stage_results
            assert StageType.ALPHA in result_state.stage_results

    @pytest.mark.asyncio
    async def test_full_pipeline_all_stages(self):
        """Test pipeline with all stages."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)

            stages = [
                DataStage(),
                AlphaEvolveAdapter(),
                RiskStage(),
                MonitoringStage(),
            ]
            approval_gate = MockApprovalGate(auto_approve=True)

            loop = PipelineLoop(
                stages=stages,
                approval_gate=approval_gate,
                checkpoint_dir=checkpoint_dir,
            )

            state = PipelineState.create(
                config={
                    "data_path": "./test_data.parquet",
                    "min_records": 1,
                    "evolution_generations": 3,
                    "max_leverage": 2.0,
                }
            )

            result_state = await loop.run(state)

            assert result_state.status == PipelineStatus.COMPLETED
            assert len(result_state.stage_results) == 4

    @pytest.mark.asyncio
    async def test_pipeline_checkpoint_resume(self):
        """Test checkpoint and resume functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)

            # Run first stage only
            stages = [DataStage()]
            approval_gate = MockApprovalGate(auto_approve=True)

            loop = PipelineLoop(
                stages=stages,
                approval_gate=approval_gate,
                checkpoint_dir=checkpoint_dir,
            )

            state = PipelineState.create(config={"data_path": "./test.parquet", "min_records": 1})

            result_state = await loop.run(state)
            checkpoint_path = result_state.save_checkpoint(checkpoint_dir)

            # Resume with more stages
            resumed_state = PipelineState.load_checkpoint(checkpoint_path)
            assert resumed_state.pipeline_id == state.pipeline_id
            assert StageType.DATA in resumed_state.stage_results

    @pytest.mark.asyncio
    async def test_pipeline_approval_rejection(self):
        """Test pipeline stops on approval rejection."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)

            # Use adapter that always triggers review
            adapter = AlphaEvolveAdapter(min_fitness=0.99)  # High threshold

            stages = [DataStage(), adapter]
            approval_gate = MockApprovalGate(auto_approve=False)

            loop = PipelineLoop(
                stages=stages,
                approval_gate=approval_gate,
                checkpoint_dir=checkpoint_dir,
            )

            state = PipelineState.create(
                config={
                    "data_path": "./test.parquet",
                    "min_records": 1,
                    "evolution_generations": 2,
                }
            )

            result_state = await loop.run(state)

            # Should fail due to rejection
            assert result_state.status == PipelineStatus.FAILED
            assert len(approval_gate.approval_requests) > 0

    @pytest.mark.asyncio
    async def test_pipeline_progress_callbacks(self):
        """Test progress callbacks are called."""
        with tempfile.TemporaryDirectory() as tmpdir:
            checkpoint_dir = Path(tmpdir)
            progress_events = []

            def on_progress(event):
                progress_events.append(event)

            stages = [DataStage(), MonitoringStage()]
            approval_gate = MockApprovalGate(auto_approve=True)

            loop = PipelineLoop(
                stages=stages,
                approval_gate=approval_gate,
                checkpoint_dir=checkpoint_dir,
            )
            loop.add_callback(on_progress)

            state = PipelineState.create(config={"data_path": "./test.parquet", "min_records": 1})

            await loop.run(state)

            assert len(progress_events) > 0
            # Should have start, stage updates, and completion
            statuses = [e.status for e in progress_events]
            assert PipelineStatus.RUNNING in statuses


class TestAlphaEvolveAdapter:
    """Test Alpha-Evolve adapter specifically."""

    def test_stage_type(self):
        """Test adapter has ALPHA stage type."""
        adapter = AlphaEvolveAdapter()
        assert adapter.stage_type == StageType.ALPHA

    def test_depends_on_data(self):
        """Test adapter depends on DATA."""
        adapter = AlphaEvolveAdapter()
        assert StageType.DATA in adapter.get_dependencies()

    @pytest.mark.asyncio
    async def test_standalone_execution(self):
        """Test adapter runs standalone (without controller)."""
        adapter = AlphaEvolveAdapter()
        state = PipelineState.create(config={"evolution_generations": 5, "population_size": 10})

        # Add mock data result
        from pipeline.core.types import StageResult

        state.stage_results[StageType.DATA] = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={"source": "test", "record_count": 1000},
        )

        result = await adapter.execute(state)

        assert result.stage == StageType.ALPHA
        assert result.status == PipelineStatus.COMPLETED
        assert result.output is not None
        assert "best_fitness" in result.output

    @pytest.mark.asyncio
    async def test_high_fitness_threshold(self):
        """Test high fitness threshold triggers review."""
        adapter = AlphaEvolveAdapter(min_fitness=0.99)
        state = PipelineState.create(config={"evolution_generations": 3})

        from pipeline.core.types import StageResult

        state.stage_results[StageType.DATA] = StageResult(
            stage=StageType.DATA,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output={"source": "test", "record_count": 1000},
        )

        result = await adapter.execute(state)

        # Should need review due to fitness below 0.99
        assert result.needs_human_review is True
        assert result.confidence != Confidence.HIGH_CONFIDENCE
