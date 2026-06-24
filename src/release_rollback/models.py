from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Decision = Literal["continue", "pause", "rollback"]
Severity = Literal["low", "medium", "high", "critical"]


class ReleaseEvidence(BaseModel):
    service: str = Field(min_length=1)
    environment: str = Field(default="production", min_length=1)
    version: str = Field(min_length=1)
    deployment_age_minutes: int = Field(ge=0)
    error_rate_percent: float = Field(ge=0)
    baseline_error_rate_percent: float = Field(ge=0)
    p95_latency_ms: float = Field(ge=0)
    baseline_p95_latency_ms: float = Field(ge=0)
    saturation_percent: float = Field(ge=0, le=100)
    failed_synthetic_checks: int = Field(ge=0)
    canary_traffic_percent: float = Field(ge=0, le=100)
    customer_impact_count: int = Field(ge=0)
    open_sev1_incident: bool = False
    change_freeze_active: bool = False
    runbook_url: str | None = None


class TriggeredRule(BaseModel):
    rule: str
    points: int
    message: str


class DecisionReport(BaseModel):
    service: str
    environment: str
    version: str
    decision: Decision
    severity: Severity
    score: int
    triggered_rules: list[TriggeredRule]
    recommended_actions: list[str]
    summary: str
