import logging

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.incident import Incident, IncidentStatus
from app.routers.incidents import run_analysis
from app.schemas.incident import GenericAlert, GrafanaAlert

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

GRAFANA_SEVERITY_MAP = {
    "critical": "critical",
    "high": "high",
    "warning": "medium",
    "info": "low",
    "alerting": "high",
    "ok": "low",
}


@router.post("/grafana", status_code=202)
async def grafana_webhook(
    payload: GrafanaAlert, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    severity = GRAFANA_SEVERITY_MAP.get(payload.state.lower(), "medium")
    metrics = {m["metric"]: m["value"] for m in payload.evalMatches if "metric" in m and "value" in m}

    incident = Incident(
        title=payload.ruleName or payload.title,
        service_name=payload.tags.get("service", "unknown"),
        severity=severity,
        source="grafana",
        alert_payload=payload.model_dump(),
        log_snippets=[payload.message] if payload.message else [],
        metrics_data=metrics,
        status=IncidentStatus.received,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    background_tasks.add_task(run_analysis, incident.id)

    logger.info("Grafana alert ingested as incident %d (severity=%s)", incident.id, severity)
    return {"incident_id": incident.id, "status": "received", "severity": severity}


@router.post("/generic", status_code=202)
async def generic_webhook(
    payload: GenericAlert, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    incident = Incident(
        title=payload.title,
        service_name=payload.service,
        severity=payload.severity,
        source=payload.source,
        alert_payload=payload.model_dump(),
        log_snippets=payload.logs,
        metrics_data=payload.metrics,
        status=IncidentStatus.received,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    background_tasks.add_task(run_analysis, incident.id)

    logger.info("Generic alert ingested as incident %d", incident.id)
    return {"incident_id": incident.id, "status": "received"}
