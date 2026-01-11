#!/usr/bin/env python
"""
Simple pipeline example.

Run with:
    python -m pipeline.examples.simple_pipeline
"""

import asyncio
import tempfile
from pathlib import Path

from pipeline.core.loop import PipelineLoop
from pipeline.core.state import PipelineState
from pipeline.core.types import PipelineStatus
from pipeline.hitl.approval import ApprovalGate
from pipeline.stages.data import DataStage
from pipeline.stages.monitoring import MonitoringStage


def on_progress(event):
    """Progress callback."""
    status_icons = {
        PipelineStatus.RUNNING: "->",
        PipelineStatus.COMPLETED: "OK",
        PipelineStatus.FAILED: "XX",
        PipelineStatus.PENDING_APPROVAL: "??",
    }
    icon = status_icons.get(event.status, "--")
    print(f"[{icon}] {event.stage.value}: {event.message}")


async def main():
    """Run a simple pipeline."""
    print("=" * 60)
    print("Simple Pipeline Example")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        checkpoint_dir = Path(tmpdir)

        # Create minimal stages
        stages = [
            DataStage(),
            MonitoringStage(),
        ]

        # Auto-approve for demo
        class AutoApprovalGate(ApprovalGate):
            async def request_approval(self, pipeline_id, result):
                from pipeline.hitl.approval import ApprovalResponse

                print(f"  [Auto-approved: {result.stage.value}]")
                return ApprovalResponse(approved=True, action="approve", reviewer="auto")

        # Create loop
        loop = PipelineLoop(
            stages=stages,
            approval_gate=AutoApprovalGate(),
            checkpoint_dir=checkpoint_dir,
            auto_checkpoint=True,
        )
        loop.add_callback(on_progress)

        # Create state with minimal config
        state = PipelineState.create(
            config={
                "data_path": "./data/test.parquet",
                "min_records": 1,  # Low threshold for demo
            }
        )

        print(f"\nPipeline ID: {state.pipeline_id}")
        print(f"Checkpoint dir: {checkpoint_dir}\n")

        # Run pipeline
        result = await loop.run(state)

        # Output results
        print("\n" + "=" * 60)
        print(f"Final Status: {result.status.name}")
        print(f"Stages Completed: {len(result.stage_results)}")

        for stage_type, stage_result in result.stage_results.items():
            print(f"  - {stage_type.value}: {stage_result.confidence.name}")

        if result.checkpoint_path:
            print(f"\nCheckpoint saved: {result.checkpoint_path}")

        return 0 if result.status == PipelineStatus.COMPLETED else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
