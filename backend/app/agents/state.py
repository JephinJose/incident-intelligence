from typing import TypedDict


class IncidentState(TypedDict):
    incident_id: int
    service_name: str
    severity: str
    title: str
    alert_payload: dict
    log_snippets: list[str]
    metrics_data: dict

    log_analysis: str
    metrics_analysis: str
    root_cause: str
    confidence: float
    contributing_factors: list[str]
    runbook: str
    summary: str

    steps: list[dict]
    error: str | None
