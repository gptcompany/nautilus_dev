"""
Data stage implementation.

Handles data loading, validation, and preparation for the pipeline.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pipeline.core.state import PipelineState
from pipeline.core.types import (
    Confidence,
    PipelineStatus,
    StageResult,
    StageType,
    ValidationResult,
)
from pipeline.hitl.confidence import ConfidenceScorer, create_validation_from_check
from pipeline.stages.base import AbstractStage


@dataclass
class DataConfig:
    """Configuration for data stage."""

    data_path: Path | str | None = None
    catalog_path: Path | str | None = None
    symbols: list[str] = field(default_factory=list)
    start_date: str | None = None
    end_date: str | None = None
    min_records: int = 100
    validate_quality: bool = True


class DataStage(AbstractStage):
    """
    Data loading and validation stage.

    Responsibilities:
        - Load data from catalog or files
        - Validate data quality
        - Prepare data for downstream stages

    Example:
        ```python
        stage = DataStage()
        state = PipelineState.create(config={
            "data_path": "./data/BTCUSDT.parquet",
            "min_records": 1000,
        })
        result = await stage.execute(state)
        ```
    """

    def __init__(self, confidence_scorer: ConfidenceScorer | None = None):
        """
        Initialize data stage.

        Args:
            confidence_scorer: Custom scorer, or default if None
        """
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()

    @property
    def stage_type(self) -> StageType:
        """Return stage type."""
        return StageType.DATA

    def validate_input(self, state: PipelineState) -> bool:
        """Validate inputs before execution."""
        config = state.config
        # Need either data_path or catalog_path
        return bool(config.get("data_path") or config.get("catalog_path"))

    def get_dependencies(self) -> list[StageType]:
        """Data stage has no dependencies."""
        return []

    async def execute(self, state: PipelineState) -> StageResult:
        """
        Execute data loading and validation.

        Args:
            state: Pipeline state with config

        Returns:
            StageResult with loaded data
        """
        config = self._parse_config(state.config)
        validations: list[ValidationResult] = []

        try:
            # Load data
            data = await self._load_data(config)

            # Validate
            validations = await self._validate_data(data, config)

            # Score confidence
            confidence = self.confidence_scorer.score(validations)

            # Build metadata
            metadata = self._build_metadata(data, validations)

            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.COMPLETED,
                confidence=confidence,
                output=data,
                metadata=metadata,
                needs_human_review=confidence in (Confidence.LOW_CONFIDENCE, Confidence.CONFLICT),
                review_reason=self._get_review_reason(validations, confidence),
            )

        except Exception as e:
            return StageResult(
                stage=self.stage_type,
                status=PipelineStatus.FAILED,
                confidence=Confidence.UNSOLVABLE,
                output=None,
                metadata={"error": str(e)},
                needs_human_review=True,
                review_reason=f"Data loading failed: {e}",
            )

    def _parse_config(self, config: dict[str, Any]) -> DataConfig:
        """Parse config dict into DataConfig."""
        return DataConfig(
            data_path=config.get("data_path"),
            catalog_path=config.get("catalog_path"),
            symbols=config.get("symbols", []),
            start_date=config.get("start_date"),
            end_date=config.get("end_date"),
            min_records=config.get("min_records", 100),
            validate_quality=config.get("validate_quality", True),
        )

    async def _load_data(self, config: DataConfig) -> dict[str, Any]:
        """
        Load data from source.

        Override this method for custom data loading logic.
        """
        data: dict[str, Any] = {
            "source": None,
            "records": [],
            "record_count": 0,
            "symbols": config.symbols,
        }

        if config.data_path:
            data["source"] = str(config.data_path)
            # Placeholder - actual loading would use pandas/parquet
            data["record_count"] = await self._count_records(config.data_path)

        elif config.catalog_path:
            data["source"] = str(config.catalog_path)
            # Placeholder - actual loading would use ParquetDataCatalog
            data["record_count"] = await self._count_records(config.catalog_path)

        return data

    async def _count_records(self, path: Path | str) -> int:
        """Count records in data file (placeholder)."""
        # In real implementation, would count actual records
        path = Path(path)
        if path.exists():
            # Estimate based on file size (placeholder)
            return max(1000, int(path.stat().st_size / 100))
        return 0

    async def _validate_data(
        self,
        data: dict[str, Any],
        config: DataConfig,
    ) -> list[ValidationResult]:
        """Run data validations."""
        validations = []

        # Check record count
        record_count = data.get("record_count", 0)
        count_ok = record_count >= config.min_records
        validations.append(
            create_validation_from_check(
                source="record_count",
                passed=count_ok,
                score=min(1.0, record_count / config.min_records)
                if config.min_records > 0
                else 1.0,
                message=f"Found {record_count} records (min: {config.min_records})",
            )
        )

        # Check data source exists
        source = data.get("source")
        source_ok = source is not None
        validations.append(
            create_validation_from_check(
                source="data_source",
                passed=source_ok,
                score=1.0 if source_ok else 0.0,
                message=f"Data source: {source}" if source_ok else "No data source",
            )
        )

        # Quality validation (placeholder)
        if config.validate_quality:
            validations.append(
                create_validation_from_check(
                    source="quality_check",
                    passed=True,
                    score=0.9,  # Placeholder score
                    message="Quality check passed",
                )
            )

        return validations

    def _build_metadata(
        self,
        data: dict[str, Any],
        validations: list[ValidationResult],
    ) -> dict[str, Any]:
        """Build metadata dict."""
        return {
            "source": data.get("source"),
            "record_count": data.get("record_count", 0),
            "symbols": data.get("symbols", []),
            "validations_passed": sum(1 for v in validations if v.passed),
            "validations_total": len(validations),
        }

    def _get_review_reason(
        self,
        validations: list[ValidationResult],
        confidence: Confidence,
    ) -> str | None:
        """Get review reason if needed."""
        if confidence == Confidence.HIGH_CONFIDENCE:
            return None

        failed = [v for v in validations if not v.passed]
        if failed:
            return f"Validation issues: {', '.join(v.source for v in failed)}"

        if confidence == Confidence.CONFLICT:
            return "Validation sources disagree"

        return "Data quality below threshold"
