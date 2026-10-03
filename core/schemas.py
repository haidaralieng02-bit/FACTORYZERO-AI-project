from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, ConfigDict

Status = Literal["WAITING", "RUNNING", "COMPLETED", "WARNING", "FAILED"]

class Hypothesis(BaseModel):
    hypothesis: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    supporting_observations: list[str] = Field(default_factory=list)
    evidence_needed: list[str] = Field(default_factory=list)

class EvidenceItem(BaseModel):
    source: str
    document: str
    page: int | None = None
    relevant_passage: str
    supported_hypothesis: str
    support_level: Literal["HIGH", "MEDIUM", "LOW", "NONE"]
    score: float = Field(ge=0.0, le=1.0)

class TelemetryResult(BaseModel):
    status: str
    severity: Literal["NORMAL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
    observations: list[str] = Field(default_factory=list)
    detected_parameters: list[str] = Field(default_factory=list)
    threshold_breaches: list[dict[str, Any]] = Field(default_factory=list)
    trend_summary: str = ""
    possible_domains: list[str] = Field(default_factory=list)
    statistics: dict[str, Any] = Field(default_factory=dict)

class MaintenancePlan(BaseModel):
    immediate_actions: list[str] = Field(default_factory=list)
    inspection_sequence: list[str] = Field(default_factory=list)
    repair_actions: list[str] = Field(default_factory=list)
    required_parts: list[str] = Field(default_factory=list)
    required_tools: list[str] = Field(default_factory=list)
    estimated_downtime_hours: float = Field(default=0.0, ge=0.0)
    priority: Literal["Immediate", "High", "Medium", "Low"] = "Medium"
    safety_notes: list[str] = Field(default_factory=list)

class ProductionImpact(BaseModel):
    production_rate_units_per_hour: float = Field(default=0.0, ge=0.0)
    downtime_hours: float = Field(default=0.0, ge=0.0)
    estimated_production_impact_units: float = Field(default=0.0, ge=0.0)
    maintenance_window: str = ""
    operational_notes: list[str] = Field(default_factory=list)

class VerificationResult(BaseModel):
    status: Literal["PASS", "REVISE", "FAIL"]
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: dict[str, bool] = Field(default_factory=dict)

class AgentEvent(BaseModel):
    agent: str
    status: Status
    timestamp: str
    input_summary: str = ""
    output_summary: str = ""
    confidence: float | None = None

class IncidentState(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    incident_id: str
    machine_id: str
    machine_name: str
    telemetry_summary: dict[str, Any] = Field(default_factory=dict)
    sensor_result: TelemetryResult | None = None
    electrical_hypotheses: list[Hypothesis] = Field(default_factory=list)
    mechanical_hypotheses: list[Hypothesis] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    maintenance_plan: MaintenancePlan | None = None
    production_impact: ProductionImpact | None = None
    verification: VerificationResult | None = None
    agent_events: list[AgentEvent] = Field(default_factory=list)
    final_status: str = "NOT_RUN"
    mode: Literal["LIVE", "DEMO"] = "DEMO"
    source_files: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)

    def to_report_dict(self):
        return self.model_dump(mode="json")
