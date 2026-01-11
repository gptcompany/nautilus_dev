"""
CLI interface for pipeline control.

Usage:
    python -m pipeline.cli run --config config.yaml
    python -m pipeline.cli resume --checkpoint ./checkpoints/pipeline_abc.json
    python -m pipeline.cli status --pipeline-id abc123
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from pipeline.alpha.evolve.adapter import AlphaEvolveAdapter
from pipeline.core.loop import PipelineLoop
from pipeline.core.state import PipelineState
from pipeline.core.types import PipelineStatus
from pipeline.hitl.approval import ApprovalGate
from pipeline.hitl.notifications import (
    create_notification_service,
)
from pipeline.stages.data import DataStage
from pipeline.stages.monitoring import MonitoringStage
from pipeline.stages.risk import RiskStage


def create_stages(config: dict) -> list:
    """Create pipeline stages based on config."""
    stages = []

    # Data stage (always included)
    stages.append(DataStage())

    # Alpha stage (optional)
    if config.get("enable_alpha", True):
        stages.append(AlphaEvolveAdapter())

    # Risk stage (optional)
    if config.get("enable_risk", True):
        stages.append(RiskStage())

    # Monitoring stage (optional)
    if config.get("enable_monitoring", True):
        stages.append(MonitoringStage())

    return stages


def load_config(config_path: Path) -> dict:
    """Load configuration from file."""
    if config_path.suffix == ".json":
        with open(config_path) as f:
            return json.load(f)
    elif config_path.suffix in (".yaml", ".yml"):
        try:
            import yaml

            with open(config_path) as f:
                return yaml.safe_load(f)
        except ImportError:
            print("PyYAML not installed. Use JSON config or install pyyaml.")
            sys.exit(1)
    else:
        print(f"Unsupported config format: {config_path.suffix}")
        sys.exit(1)


def on_progress(event):
    """Progress callback for CLI output."""
    status_emoji = {
        PipelineStatus.RUNNING: "🔄",
        PipelineStatus.COMPLETED: "✅",
        PipelineStatus.FAILED: "❌",
        PipelineStatus.PENDING_APPROVAL: "⏸️",
    }
    emoji = status_emoji.get(event.status, "📊")
    print(
        f"{emoji} [{event.pipeline_id}] {event.stage.value}: {event.status.name} - {event.message}"
    )


async def run_pipeline(args):
    """Run pipeline from config."""
    # Load config
    if args.config:
        config = load_config(Path(args.config))
    else:
        config = {}

    # Override with CLI args
    if args.data_path:
        config["data_path"] = args.data_path
    if args.catalog_path:
        config["catalog_path"] = args.catalog_path

    # Create stages
    stages = create_stages(config)

    # Create approval gate
    notification_service = create_notification_service(
        discord_webhook_url=config.get("discord_webhook")
    )
    approval_gate = ApprovalGate(
        notification_service=notification_service,
        approval_dir=Path(args.approval_dir) if args.approval_dir else None,
    )

    # Create loop
    checkpoint_dir = Path(args.checkpoint_dir)
    loop = PipelineLoop(
        stages=stages,
        approval_gate=approval_gate,
        checkpoint_dir=checkpoint_dir,
        auto_checkpoint=not args.no_checkpoint,
    )
    loop.add_callback(on_progress)

    # Create state
    state = PipelineState.create(config=config)
    print(f"Starting pipeline {state.pipeline_id}")

    # Run
    result_state = await loop.run(state)

    # Output result
    print(f"\nPipeline {result_state.status.name}")
    print(f"Stages completed: {len(result_state.stage_results)}")

    if result_state.checkpoint_path:
        print(f"Checkpoint: {result_state.checkpoint_path}")

    return 0 if result_state.status == PipelineStatus.COMPLETED else 1


async def resume_pipeline(args):
    """Resume pipeline from checkpoint."""
    checkpoint_path = Path(args.checkpoint)

    if not checkpoint_path.exists():
        print(f"Checkpoint not found: {checkpoint_path}")
        return 1

    # Load state
    state = PipelineState.load_checkpoint(checkpoint_path)
    print(f"Resuming pipeline {state.pipeline_id} from stage {state.current_stage}")

    # Create stages and loop
    stages = create_stages(state.config)
    approval_gate = ApprovalGate()
    checkpoint_dir = checkpoint_path.parent

    loop = PipelineLoop(
        stages=stages,
        approval_gate=approval_gate,
        checkpoint_dir=checkpoint_dir,
    )
    loop.add_callback(on_progress)

    # Run
    result_state = await loop.run(state)

    print(f"\nPipeline {result_state.status.name}")
    return 0 if result_state.status == PipelineStatus.COMPLETED else 1


async def show_status(args):
    """Show pipeline status from checkpoint."""
    checkpoint_dir = Path(args.checkpoint_dir)

    if args.pipeline_id:
        # Find specific checkpoint
        checkpoint_path = checkpoint_dir / f"pipeline_{args.pipeline_id}.json"
        if not checkpoint_path.exists():
            print(f"Pipeline {args.pipeline_id} not found")
            return 1

        state = PipelineState.load_checkpoint(checkpoint_path)
        _print_state(state)
    else:
        # List all checkpoints
        checkpoints = list(checkpoint_dir.glob("pipeline_*.json"))
        if not checkpoints:
            print("No pipelines found")
            return 0

        print(f"Found {len(checkpoints)} pipeline(s):\n")
        for cp in checkpoints:
            try:
                state = PipelineState.load_checkpoint(cp)
                print(f"  {state.pipeline_id}: {state.status.name} (stage: {state.current_stage})")
            except Exception as e:
                print(f"  {cp.stem}: Error loading - {e}")

    return 0


def _print_state(state: PipelineState):
    """Print pipeline state details."""
    print(f"Pipeline ID: {state.pipeline_id}")
    print(f"Status: {state.status.name}")
    print(f"Current Stage: {state.current_stage}")
    print(f"Created: {state.created_at}")
    print(f"Updated: {state.updated_at}")
    print("\nStage Results:")
    for stage_type, result in state.stage_results.items():
        print(f"  {stage_type.value}: {result.status.name} ({result.confidence.name})")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Trading Pipeline Framework CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run new pipeline")
    run_parser.add_argument("--config", "-c", help="Config file (JSON/YAML)")
    run_parser.add_argument("--data-path", help="Data file path")
    run_parser.add_argument("--catalog-path", help="Catalog path")
    run_parser.add_argument(
        "--checkpoint-dir",
        default="./checkpoints",
        help="Checkpoint directory",
    )
    run_parser.add_argument("--approval-dir", help="Approval files directory")
    run_parser.add_argument(
        "--no-checkpoint",
        action="store_true",
        help="Disable auto-checkpoint",
    )

    # Resume command
    resume_parser = subparsers.add_parser("resume", help="Resume from checkpoint")
    resume_parser.add_argument("checkpoint", help="Checkpoint file path")

    # Status command
    status_parser = subparsers.add_parser("status", help="Show pipeline status")
    status_parser.add_argument("--pipeline-id", "-p", help="Pipeline ID")
    status_parser.add_argument(
        "--checkpoint-dir",
        default="./checkpoints",
        help="Checkpoint directory",
    )

    args = parser.parse_args()

    if args.command == "run":
        return asyncio.run(run_pipeline(args))
    elif args.command == "resume":
        return asyncio.run(resume_pipeline(args))
    elif args.command == "status":
        return asyncio.run(show_status(args))
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
