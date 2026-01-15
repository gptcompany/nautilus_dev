# Trading Pipeline Framework with HITL

A standardized pipeline framework with Human-in-the-Loop (HITL) capabilities for trading system development.

## Overview

The pipeline executes stages in sequence with confidence-based approval gates:

```
DATA → ALPHA → RISK → EXECUTION → MONITORING
```

Each stage produces a `StageResult` with a confidence score. Low confidence results pause the pipeline for human review.

## Quick Start

### CLI Usage

```bash
# Run new pipeline
python -m pipeline.cli run --config config.yaml

# Resume from checkpoint
python -m pipeline.cli resume ./checkpoints/pipeline_abc123.json

# Check status
python -m pipeline.cli status --pipeline-id abc123
```

### Programmatic Usage

```python
import asyncio
from pathlib import Path

from pipeline.core.loop import PipelineLoop
from pipeline.core.state import PipelineState
from pipeline.hitl.approval import ApprovalGate
from pipeline.stages.data import DataStage
from pipeline.stages.alpha import AlphaStage
from pipeline.stages.risk import RiskStage
from pipeline.stages.monitoring import MonitoringStage

async def main():
    # Create stages
    stages = [
        DataStage(),
        AlphaStage(),
        RiskStage(),
        MonitoringStage(),
    ]

    # Create approval gate
    approval_gate = ApprovalGate()

    # Create pipeline loop
    loop = PipelineLoop(
        stages=stages,
        approval_gate=approval_gate,
        checkpoint_dir=Path("./checkpoints"),
        auto_checkpoint=True,
    )

    # Add progress callback
    loop.add_callback(lambda e: print(f"{e.stage.value}: {e.status.name}"))

    # Create initial state
    state = PipelineState.create(
        config={
            "data_path": "./data/BTCUSDT.parquet",
            "min_records": 1000,
            "model_type": "momentum",
            "max_leverage": 2.0,
        }
    )

    # Run pipeline
    result = await loop.run(state)
    print(f"Pipeline {result.status.name}")

asyncio.run(main())
```

## Profiles

Three complexity levels integrating ML modules from `strategies/common/`:

| Profile | Features | Use Case |
|---------|----------|----------|
| **BASIC** | Standard orchestration | Rule-based strategies |
| **ML_LITE** | + Regime Detection + Giller Sizing | Hybrid strategies |
| **ML_FULL** | + Walk-Forward + Triple Barrier + Meta-Labeling | ML strategies |

```python
from pipeline.profiles import PipelineProfile, create_pipeline

pipeline = create_pipeline(PipelineProfile.ML_LITE)
```

See `pipeline/profiles/README.md` for full documentation.

## Architecture

### Core Components

```
pipeline/
├── core/
│   ├── types.py      # PipelineStatus, Confidence, StageType, StageResult
│   ├── state.py      # PipelineState with checkpoint/resume
│   └── loop.py       # Main pipeline loop with HITL gates
├── hitl/
│   ├── approval.py   # ApprovalGate, file-based approval waiting
│   ├── confidence.py # ConfidenceScorer (multi-CAS pattern)
│   ├── notifications.py # Discord/Console notifications
│   └── prompts.py    # Human review prompt templates
├── stages/
│   ├── base.py       # AbstractStage interface
│   ├── data.py       # Data validation stage
│   ├── alpha.py      # Alpha/signal generation stage
│   ├── risk.py       # Risk management stage (FIXED limits)
│   └── monitoring.py # Metrics and alerting stage
└── alpha/
    └── evolve/
        └── adapter.py # Alpha-Evolve integration
```

### Confidence Levels

| Level | Description | Action |
|-------|-------------|--------|
| `HIGH_CONFIDENCE` | All validations pass | Auto-proceed |
| `MEDIUM_CONFIDENCE` | Most validations pass | Log, proceed with caution |
| `LOW_CONFIDENCE` | Validation issues | **Require human review** |
| `CONFLICT` | Sources disagree | **Require human review** |
| `UNSOLVABLE` | Cannot determine | **Escalate** |

### Pipeline Status

| Status | Description |
|--------|-------------|
| `IDLE` | Not started |
| `RUNNING` | Executing stages |
| `PAUSED` | Manually paused |
| `PENDING_APPROVAL` | Waiting for human review |
| `COMPLETED` | All stages finished |
| `FAILED` | Stage failed or rejected |

## Stage Implementations

### DataStage

Validates data availability and quality.

```python
state = PipelineState.create(config={
    "data_path": "./data/BTCUSDT.parquet",  # or catalog_path
    "min_records": 1000,
    "symbols": ["BTCUSDT", "ETHUSDT"],
    "validate_quality": True,
})
```

### AlphaStage

Generates trading signals/alphas.

```python
state = PipelineState.create(config={
    "model_type": "momentum",  # or "mean_reversion", "ml"
    "min_sharpe": 0.5,
    "max_overfitting": 0.3,
})
```

### RiskStage

Applies position sizing and risk limits. **Safety limits are FIXED** (per CLAUDE.md):

```python
# These are FIXED - never adaptive (Knight Capital $440M lesson)
MAX_LEVERAGE = 3.0
MAX_POSITION_PCT = 10.0
STOP_LOSS_PCT = 5.0
DAILY_LOSS_LIMIT_PCT = 2.0
KILL_SWITCH_DRAWDOWN = 15.0
```

### MonitoringStage

Configures metrics collection and alerts.

```python
state = PipelineState.create(config={
    "metrics": ["pnl", "drawdown", "leverage", "win_rate"],
    "alert_drawdown_pct": 10.0,
    "discord_webhook": "https://discord.com/api/webhooks/...",
})
```

## Human-in-the-Loop

### Approval Gate

When a stage returns `LOW_CONFIDENCE` or `CONFLICT`, the pipeline pauses and requests human approval.

**File-based approval** (default):
```bash
# Pipeline creates: ./approvals/pipeline_abc123_alpha_request.json
# Human creates:    ./approvals/pipeline_abc123_alpha_approved.json

# Approval file content:
{
    "approved": true,
    "action": "approve",
    "reviewer": "sam",
    "comments": "Looks good"
}
```

**Discord notification** (optional):
```python
from pipeline.hitl.notifications import create_notification_service

notification_service = create_notification_service(
    discord_webhook_url="https://discord.com/api/webhooks/..."
)
approval_gate = ApprovalGate(notification_service=notification_service)
```

### Confidence Scoring

Multi-CAS (Consensus Aggregation System) pattern:

```python
from pipeline.hitl.confidence import ConfidenceScorer, ConfidenceThresholds

scorer = ConfidenceScorer(
    thresholds=ConfidenceThresholds(
        high=0.85,   # All sources agree, high scores
        medium=0.65, # Most sources agree
        low=0.4,     # Disagreement or low scores
    )
)

# Score from multiple validation results
confidence = scorer.score(validations)
```

## Checkpoint/Resume

Pipelines automatically checkpoint after each stage:

```python
# Checkpoint saved to: ./checkpoints/pipeline_abc123.json
state.save_checkpoint(checkpoint_dir)

# Resume from checkpoint
state = PipelineState.load_checkpoint(checkpoint_path)
loop = PipelineLoop(stages=stages, ...)
result = await loop.run(state)  # Continues from last completed stage
```

## Alpha-Evolve Integration

The `AlphaEvolveAdapter` wraps existing Alpha-Evolve for pipeline integration:

```python
from pipeline.alpha.evolve.adapter import AlphaEvolveAdapter
from scripts.alpha_evolve.controller import AlphaEvolveController

# With existing controller
controller = AlphaEvolveController(config)
adapter = AlphaEvolveAdapter(
    controller=controller,
    min_fitness=0.6,
    max_generations=50,
)

# Standalone (for testing)
adapter = AlphaEvolveAdapter()

# Use in pipeline
stages = [DataStage(), adapter, RiskStage(), MonitoringStage()]
```

## Configuration

### Example config.yaml

```yaml
# Data
data_path: ./data/BTCUSDT_1h.parquet
min_records: 5000
symbols:
  - BTCUSDT
  - ETHUSDT

# Alpha
model_type: momentum
min_sharpe: 1.0
max_overfitting: 0.25
evolution_generations: 20
population_size: 50

# Risk (fixed limits)
max_leverage: 2.0
stop_loss_pct: 3.0

# Monitoring
alert_drawdown_pct: 8.0
discord_webhook: ${DISCORD_WEBHOOK}
enable_console: true
dashboard_enabled: true
```

## Testing

```bash
# Run all pipeline tests
uv run pytest tests/pipeline/ -v

# Run specific test class
uv run pytest tests/pipeline/test_integration.py::TestFullPipelineExecution -v

# Run with coverage
uv run pytest tests/pipeline/ --cov=pipeline --cov-report=term-missing
```

## Creating Custom Stages

```python
from pipeline.stages.base import AbstractStage
from pipeline.core.types import StageType, StageResult, PipelineStatus, Confidence
from pipeline.core.state import PipelineState

class MyCustomStage(AbstractStage):
    @property
    def stage_type(self) -> StageType:
        return StageType.ALPHA  # or add new StageType

    def validate_input(self, state: PipelineState) -> bool:
        # Check prerequisites
        return StageType.DATA in state.stage_results

    def get_dependencies(self) -> list[StageType]:
        return [StageType.DATA]

    def get_confidence_requirement(self) -> Confidence:
        return Confidence.MEDIUM_CONFIDENCE

    async def execute(self, state: PipelineState) -> StageResult:
        # Your logic here
        result = await self._do_work(state)

        return StageResult(
            stage=self.stage_type,
            status=PipelineStatus.COMPLETED,
            confidence=Confidence.HIGH_CONFIDENCE,
            output=result,
            needs_human_review=False,
        )
```

## License

Internal use only.
