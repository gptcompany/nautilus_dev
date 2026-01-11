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
    # Quality thresholds
    max_missing_pct: float = 5.0  # Max allowed missing values %
    max_duplicates_pct: float = 1.0  # Max allowed duplicate rows %


class DataStage(AbstractStage):
    """
    Data loading and validation stage.

    Responsibilities:
        - Load data from catalog or parquet files
        - Validate data quality (nulls, duplicates, gaps)
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
            max_missing_pct=config.get("max_missing_pct", 5.0),
            max_duplicates_pct=config.get("max_duplicates_pct", 1.0),
        )

    async def _load_data(self, config: DataConfig) -> dict[str, Any]:
        """
        Load data from source (parquet file or catalog).

        Returns dict with data info and statistics.
        """
        data: dict[str, Any] = {
            "source": None,
            "record_count": 0,
            "columns": [],
            "symbols": config.symbols,
            "date_range": None,
            "missing_pct": 0.0,
            "duplicates_pct": 0.0,
            "file_size_bytes": 0,
        }

        path = Path(config.data_path) if config.data_path else None
        if path is None and config.catalog_path:
            path = Path(config.catalog_path)

        if path is None:
            return data

        data["source"] = str(path)

        # Check if path exists
        if not path.exists():
            data["error"] = f"Path does not exist: {path}"
            return data

        # Handle directory (catalog) vs file
        if path.is_dir():
            data = await self._load_from_catalog(path, config, data)
        else:
            data = await self._load_from_file(path, config, data)

        return data

    async def _load_from_file(
        self, path: Path, config: DataConfig, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Load data from single parquet file."""
        try:
            import polars as pl

            # Read parquet file
            df = pl.read_parquet(path)

            data["record_count"] = len(df)
            data["columns"] = df.columns
            data["file_size_bytes"] = path.stat().st_size

            # Calculate missing percentage
            null_counts = df.null_count().row(0)
            total_cells = len(df) * len(df.columns)
            total_nulls = sum(null_counts)
            data["missing_pct"] = (total_nulls / total_cells * 100) if total_cells > 0 else 0.0

            # Calculate duplicates percentage
            unique_count = df.unique().height
            data["duplicates_pct"] = (
                ((len(df) - unique_count) / len(df) * 100) if len(df) > 0 else 0.0
            )

            # Try to get date range if timestamp column exists
            ts_cols = [
                c
                for c in df.columns
                if "time" in c.lower() or "date" in c.lower() or "ts" in c.lower()
            ]
            if ts_cols:
                ts_col = ts_cols[0]
                data["date_range"] = {
                    "start": str(df[ts_col].min()),
                    "end": str(df[ts_col].max()),
                }

            # Store schema info
            data["schema"] = {
                col: str(dtype) for col, dtype in zip(df.columns, df.dtypes, strict=False)
            }

        except ImportError:
            # Fallback to pyarrow if polars not available
            data = await self._load_with_pyarrow(path, data)
        except Exception as e:
            data["error"] = str(e)
            # Still try to get file size
            if path.exists():
                data["file_size_bytes"] = path.stat().st_size
                data["record_count"] = max(100, int(data["file_size_bytes"] / 100))  # Estimate

        return data

    async def _load_with_pyarrow(self, path: Path, data: dict[str, Any]) -> dict[str, Any]:
        """Fallback loading with pyarrow."""
        try:
            import pyarrow.parquet as pq

            parquet_file = pq.ParquetFile(path)
            metadata = parquet_file.metadata

            data["record_count"] = metadata.num_rows
            data["columns"] = parquet_file.schema.names
            data["file_size_bytes"] = path.stat().st_size

            # Schema info
            schema = parquet_file.schema_arrow
            data["schema"] = {field.name: str(field.type) for field in schema}

        except Exception as e:
            data["error"] = str(e)
            if path.exists():
                data["file_size_bytes"] = path.stat().st_size
                data["record_count"] = max(100, int(data["file_size_bytes"] / 100))

        return data

    async def _load_from_catalog(
        self, catalog_path: Path, config: DataConfig, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Load data from catalog directory (multiple parquet files)."""
        # Find all parquet files
        parquet_files = list(catalog_path.rglob("*.parquet"))
        data["file_count"] = len(parquet_files)

        if not parquet_files:
            data["error"] = f"No parquet files found in {catalog_path}"
            return data

        total_records = 0
        total_size = 0
        all_columns: set[str] = set()

        # Sample first few files to get schema and estimate total
        sample_files = parquet_files[:10]  # Sample up to 10 files

        for pf in sample_files:
            try:
                import polars as pl

                df = pl.read_parquet(pf)
                total_records += len(df)
                total_size += pf.stat().st_size
                all_columns.update(df.columns)
            except ImportError:
                # Fallback estimate
                total_size += pf.stat().st_size
                total_records += max(100, int(pf.stat().st_size / 100))
            except Exception:
                continue

        # Extrapolate for full catalog if we sampled
        if len(sample_files) < len(parquet_files):
            scale = len(parquet_files) / len(sample_files)
            total_records = int(total_records * scale)
            total_size = int(total_size * scale)

        data["record_count"] = total_records
        data["file_size_bytes"] = total_size
        data["columns"] = list(all_columns)

        return data

    async def _validate_data(
        self,
        data: dict[str, Any],
        config: DataConfig,
    ) -> list[ValidationResult]:
        """Run data validations."""
        validations = []

        # Check for loading errors
        if data.get("error"):
            validations.append(
                create_validation_from_check(
                    source="data_load",
                    passed=False,
                    score=0.0,
                    message=f"Load error: {data['error']}",
                )
            )
            return validations

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
                message=f"Found {record_count:,} records (min: {config.min_records:,})",
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

        # Quality validation
        if config.validate_quality:
            # Missing values check
            missing_pct = data.get("missing_pct", 0.0)
            missing_ok = missing_pct <= config.max_missing_pct
            validations.append(
                create_validation_from_check(
                    source="missing_values",
                    passed=missing_ok,
                    score=max(0.0, 1.0 - (missing_pct / config.max_missing_pct))
                    if config.max_missing_pct > 0
                    else 1.0,
                    message=f"Missing values: {missing_pct:.2f}% (max: {config.max_missing_pct}%)",
                )
            )

            # Duplicates check
            duplicates_pct = data.get("duplicates_pct", 0.0)
            duplicates_ok = duplicates_pct <= config.max_duplicates_pct
            validations.append(
                create_validation_from_check(
                    source="duplicates",
                    passed=duplicates_ok,
                    score=max(0.0, 1.0 - (duplicates_pct / config.max_duplicates_pct))
                    if config.max_duplicates_pct > 0
                    else 1.0,
                    message=f"Duplicates: {duplicates_pct:.2f}% (max: {config.max_duplicates_pct}%)",
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
            "columns": data.get("columns", []),
            "file_size_bytes": data.get("file_size_bytes", 0),
            "missing_pct": data.get("missing_pct", 0.0),
            "duplicates_pct": data.get("duplicates_pct", 0.0),
            "date_range": data.get("date_range"),
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
