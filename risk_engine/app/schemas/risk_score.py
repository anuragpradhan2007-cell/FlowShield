from enum import Enum
import uuid
from datetime import date as dt_date, datetime, timezone
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field, field_validator


class RiskTier(str, Enum):
    """
    Standardized worker risk tiers.
    Strictly enforced across Member 3, Member 4, and Member 5 contracts.
    """
    STABLE = "Stable"
    AT_RISK = "At Risk"
    CRITICAL = "Critical"


class MetricDetail(BaseModel):
    """
    Explainability model for an individual metric sub-score.
    Logs exact feature weights, standard deviations, and intermediate calculations
    for downstream debugging and Frontend (Member 5) explainability tooltips.
    """
    name: str = Field(..., description="Human-readable metric name")
    weight: float = Field(ge=0.0, le=1.0, description="Exact feature weight in composite score")
    raw_value: Optional[float] = Field(default=None, description="Primary raw feature value")
    normalized_score: float = Field(ge=0.0, le=100.0, description="Sub-score scaled strictly between 0.0 and 100.0")
    mean: Optional[float] = Field(default=None, description="Sample mean (e.g. daily/weekly earnings)")
    standard_deviation: Optional[float] = Field(default=None, description="Standard deviation for variance tracking")
    intermediate_calculations: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed dictionary of all intermediate statistical figures"
    )
    description: Optional[str] = Field(default=None, description="Technical description of the metric")
    tooltip: Optional[str] = Field(default=None, description="Frontend tooltip string for Member 5")

    model_config = ConfigDict(extra="allow")


class MetricsBreakdown(BaseModel):
    """
    Complete explainability breakdown stored in JSON/JSONB.
    Contains weights, sub-scores, statistical logs, and frontend tooltip metadata.
    """
    income_consistency: Optional[MetricDetail] = Field(
        default=None,
        description="Weight 30%: Coefficient of variation of income"
    )
    work_frequency: Optional[MetricDetail] = Field(
        default=None,
        description="Weight 25%: Active work days vs capacity"
    )
    recent_income_trend: Optional[MetricDetail] = Field(
        default=None,
        description="Weight 20%: Recent 7-14d rolling avg vs 60d baseline"
    )
    savings_buffer: Optional[MetricDetail] = Field(
        default=None,
        description="Weight 15%: Emergency reserves vs weekly expenses"
    )
    external_risk_factors: Optional[MetricDetail] = Field(
        default=None,
        description="Weight 10%: Weather or environmental disruptions"
    )
    raw_inputs_summary: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Summary of raw data ingested from Member 2"
    )
    explainability_notes: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Key diagnostic callouts for Member 5 tooltips"
    )

    model_config = ConfigDict(extra="allow")


class DailyIncomeRecord(BaseModel):
    """
    Single day income record provided by Member 2.
    """
    date: Union[dt_date, str] = Field(..., description="Date of the record (YYYY-MM-DD)")
    amount: float = Field(ge=0.0, description="Gross income earned on this date")
    hours_worked: Optional[float] = Field(default=None, ge=0.0, description="Optional active hours")
    trips_completed: Optional[int] = Field(default=None, ge=0, description="Optional completed tasks/trips")


class WorkerDataInput(BaseModel):
    """
    Structured worker income and transaction history prepared by Member 2.
    """
    worker_id: uuid.UUID = Field(..., description="Target worker UUID linked to Member 1 schema")
    income_history: List[DailyIncomeRecord] = Field(
        ...,
        min_length=1,
        description="Chronological series of daily worker earnings"
    )
    current_savings: float = Field(
        default=0.0,
        ge=0.0,
        description="Total current emergency savings reserve ($)"
    )
    weekly_expenses: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Average weekly expenses. If omitted, estimated from baseline income."
    )
    weather_condition: str = Field(
        default="CLEAR",
        description="External condition: 'CLEAR', 'MODERATE_RAIN', 'SEVERE_ALERT'"
    )
    external_risk_override: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Optional manual override score (0.0 to 100.0) for external risk"
    )
    expected_capacity_days: int = Field(
        default=24,
        ge=1,
        le=31,
        description="Expected active work days per month capacity (default: 24)"
    )


class RiskScoreBase(BaseModel):
    worker_id: uuid.UUID = Field(
        ...,
        description="Anonymous UUID reference linked to Member 1's worker schema"
    )
    stability_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Worker stability score bounded strictly between 0.0 and 100.0"
    )
    risk_tier: RiskTier = Field(
        ...,
        description="Categorical risk tier: 'Stable', 'At Risk', or 'Critical'"
    )
    metrics_breakdown: Union[MetricsBreakdown, Dict[str, Any]] = Field(
        default_factory=dict,
        description="JSON breakdown storing intermediate feature values, standard deviations, and weights"
    )

    @field_validator("stability_score")
    @classmethod
    def validate_score_bounds(cls, v: float) -> float:
        if not (0.0 <= v <= 100.0):
            raise ValueError(f"stability_score must be between 0.0 and 100.0, got {v}")
        return round(float(v), 2)


class RiskScoreCreate(RiskScoreBase):
    """
    Schema for persisting a newly calculated risk score.
    """
    id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional custom UUID. If omitted, generated automatically by database."
    )


class RiskScoreResponse(RiskScoreBase):
    """
    Strict Pydantic output contract for risk scores.
    """
    id: uuid.UUID = Field(..., description="Unique record UUID")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp in ISO-8601 format"
    )

    model_config = ConfigDict(from_attributes=True)


class WorkerRiskSummaryResponse(BaseModel):
    """
    Lightweight contract for Member 4's Financial Protection Engine.
    """
    worker_id: uuid.UUID
    stability_score: float = Field(ge=0.0, le=100.0)
    risk_tier: RiskTier
    anomaly_flags: List[str] = Field(default_factory=list)
    last_calculated_at: datetime

    model_config = ConfigDict(from_attributes=True)
