from datetime import datetime

from pydantic import BaseModel, Field


class AgentStepSchema(BaseModel):
    id: int
    step_order: int
    agent_name: str
    input_summary: str | None
    output: str | None
    latency_ms: int | None
    status: str

    model_config = {"from_attributes": True}


class IncidentBase(BaseModel):
    title: str
    service_name: str
    severity: str
    source: str = "generic"
    alert_payload: dict = Field(default_factory=dict)
    log_snippets: list[str] = Field(default_factory=list)
    metrics_data: dict = Field(default_factory=dict)


class IncidentCreate(IncidentBase):
    pass


class IncidentSummary(BaseModel):
    id: int
    title: str
    service_name: str
    severity: str
    status: str
    source: str
    confidence: float | None
    created_at: datetime
    analyzed_at: datetime | None
    summary: str | None

    model_config = {"from_attributes": True}


class IncidentDetail(IncidentSummary):
    alert_payload: dict
    log_snippets: list[str]
    metrics_data: dict
    log_analysis: str | None
    metrics_analysis: str | None
    root_cause: str | None
    runbook: str | None
    error_message: str | None
    agent_steps: list[AgentStepSchema]

    model_config = {"from_attributes": True}


class IncidentStats(BaseModel):
    total: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
    avg_analysis_time_seconds: float | None



class GrafanaAlert(BaseModel):
    title: str = "Grafana Alert"
    message: str = ""
    state: str = "alerting"
    ruleName: str = ""
    evalMatches: list[dict] = Field(default_factory=list)
    tags: dict = Field(default_factory=dict)


class GenericAlert(BaseModel):
    service: str
    severity: str = "medium"
    title: str
    message: str
    logs: list[str] = Field(default_factory=list)
    metrics: dict = Field(default_factory=dict)
    source: str = "generic"
