"""Pydantic models for baseline validation reports.

Provides structured models for:
    - ValidationReport: Complete validation result
    - ContenderSummary: Per-contender metrics summary
    - VerdictDetails: Statistical details for verdict
    - ComparisonRow: Table row for comparison display

Reference:
    - Lopez de Prado (2018): "Advances in Financial Machine Learning"
    - DeMiguel (2009): "Optimal Versus Naive Diversification"
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class Verdict(str, Enum):
    """Validation verdict.

    GO: Deploy adaptive sizing (beats baseline by threshold)
    WAIT: Insufficient evidence (edge below threshold)
    STOP: Use baseline (adaptive doesn't justify complexity)
    """

    GO = "GO"
    WAIT = "WAIT"
    STOP = "STOP"


class ContenderSummary(BaseModel):
    """Summary metrics for a single contender.

    Aggregates walk-forward results into key metrics.
    """

    name: str = Field(..., description="Contender identifier")
    avg_sharpe: float = Field(..., description="Average Sharpe ratio across windows")
    std_sharpe: float = Field(..., ge=0, description="Std dev of Sharpe across windows")
    max_drawdown: float = Field(..., ge=0, le=1, description="Maximum drawdown (0-1)")
    win_rate: float = Field(
        ..., ge=0, le=1, description="Fraction of profitable windows"
    )
    total_trades: int = Field(..., ge=0, description="Total trades across all windows")

    @field_validator("win_rate")
    @classmethod
    def validate_win_rate(cls, v: float) -> float:
        """Validate win rate is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError(f"win_rate must be between 0 and 1, got {v}")
        return v


class ComparisonRow(BaseModel):
    """Single row in comparison table.

    Displays one metric across all contenders with winner marked.
    """

    metric: str = Field(..., description="Metric name (e.g., 'Avg Sharpe')")
    adaptive: str = Field(..., description="Adaptive contender value")
    fixed: str = Field(..., description="Fixed contender value")
    buyhold: str = Field(default="N/A", description="Buy & Hold contender value")
    winner: str = Field(default="", description="Name of winning contender")


class VerdictDetails(BaseModel):
    """Statistical details supporting the verdict.

    Includes significance testing and confidence metrics.
    """

    verdict: Verdict
    sharpe_edge: float = Field(..., description="Adaptive Sharpe - Fixed Sharpe")
    drawdown_comparison: str = Field(..., description="Drawdown comparison text")
    t_statistic: float = Field(..., description="T-statistic for Sharpe difference")
    p_value: float = Field(..., ge=0, le=1, description="P-value for significance test")
    is_significant: bool = Field(
        ..., description="Whether result is statistically significant"
    )


class ValidationReport(BaseModel):
    """Complete validation report.

    Contains verdict, confidence, recommendations, and detailed metrics.
    """

    run_id: str = Field(..., description="Unique identifier for this validation run")
    timestamp: datetime = Field(..., description="When validation was run")
    verdict: Verdict = Field(..., description="GO/WAIT/STOP verdict")
    confidence: float = Field(..., ge=0, le=1, description="Confidence level (0-1)")
    recommendation: str = Field(..., description="Human-readable recommendation")
    contender_summaries: dict[str, ContenderSummary] = Field(
        ..., description="Per-contender summary metrics"
    )
    window_count: int = Field(..., ge=1, description="Number of walk-forward windows")
    data_start: datetime = Field(..., description="Start of data range")
    data_end: datetime = Field(..., description="End of data range")
    verdict_details: VerdictDetails | None = Field(
        default=None, description="Statistical details for verdict"
    )

    model_config = {"json_encoders": {datetime: lambda v: v.isoformat()}}
