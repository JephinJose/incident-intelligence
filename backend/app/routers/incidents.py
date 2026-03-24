import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.incident import AgentStep, Incident, IncidentStatus
from app.schemas.incident import IncidentCreate, IncidentDetail, IncidentStats, IncidentSummary

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/incidents", tags=["incidents"])


async def run_analysis(incident_id: int) -> None:
    from app.agents.graph import incident_graph
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        incident = await db.get(Incident, incident_id)
        if not incident:
            return

        incident.status = IncidentStatus.analyzing
        await db.commit()

        initial_state = {
            "incident_id": incident_id,
            "service_name": incident.service_name,
            "severity": incident.severity,
            "title": incident.title,
            "alert_payload": incident.alert_payload or {},
            "log_snippets": incident.log_snippets or [],
            "metrics_data": incident.metrics_data or {},
            "log_analysis": "",
            "metrics_analysis": "",
            "root_cause": "",
            "confidence": 0.0,
            "contributing_factors": [],
            "runbook": "",
            "summary": "",
            "steps": [],
            "error": None,
        }

        try:
            final_state = await incident_graph.ainvoke(initial_state)

            for i, step in enumerate(final_state.get("steps", [])):
                db.add(AgentStep(
                    incident_id=incident_id,
                    step_order=i,
                    agent_name=step["agent"],
                    input_summary=step.get("input", ""),
                    output=step.get("output", ""),
                    latency_ms=step.get("latency_ms"),
                    status=step.get("status", "completed"),
                ))

            incident.log_analysis = final_state.get("log_analysis")
            incident.metrics_analysis = final_state.get("metrics_analysis")
            incident.root_cause = final_state.get("root_cause")
            incident.confidence = final_state.get("confidence")
            incident.runbook = final_state.get("runbook")
            incident.summary = final_state.get("summary")
            incident.status = IncidentStatus.analyzed
            incident.analyzed_at = datetime.now(timezone.utc)

        except Exception as e:
            logger.exception("Analysis pipeline failed for incident %d", incident_id)
            incident.status = IncidentStatus.failed
            incident.error_message = str(e)

        await db.commit()


@router.get("", response_model=list[IncidentSummary])
async def list_incidents(
    severity: str | None = None,
    status: str | None = None,
    service: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    q = select(Incident).order_by(Incident.created_at.desc()).limit(limit).offset(offset)
    if severity:
        q = q.where(Incident.severity == severity)
    if status:
        q = q.where(Incident.status == status)
    if service:
        q = q.where(Incident.service_name.ilike(f"%{service}%"))
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/stats", response_model=IncidentStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total = (await db.execute(select(func.count(Incident.id)))).scalar_one()

    severity_rows = (await db.execute(
        select(Incident.severity, func.count()).group_by(Incident.severity)
    )).all()

    status_rows = (await db.execute(
        select(Incident.status, func.count()).group_by(Incident.status)
    )).all()

    analyzed = (await db.execute(
        select(Incident.created_at, Incident.analyzed_at).where(
            Incident.analyzed_at.isnot(None)
        )
    )).all()
    avg_time = None
    if analyzed:
        deltas = [(r.analyzed_at - r.created_at).total_seconds() for r in analyzed]
        avg_time = sum(deltas) / len(deltas)

    return IncidentStats(
        total=total,
        by_severity={row[0]: row[1] for row in severity_rows},
        by_status={row[0]: row[1] for row in status_rows},
        avg_analysis_time_seconds=avg_time,
    )


@router.get("/{incident_id}", response_model=IncidentDetail)
async def get_incident(incident_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Incident).options(selectinload(Incident.agent_steps)).where(Incident.id == incident_id)
    )
    incident = result.scalar_one_or_none()
    if not incident:
        raise HTTPException(404, f"Incident {incident_id} not found")
    return incident


@router.get("/{incident_id}/runbook")
async def get_runbook(incident_id: int, db: AsyncSession = Depends(get_db)):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, f"Incident {incident_id} not found")
    if not incident.runbook:
        raise HTTPException(404, "Runbook not yet generated")
    return {"incident_id": incident_id, "runbook": incident.runbook}


@router.post("/{incident_id}/analyze")
async def trigger_analysis(
    incident_id: int, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    incident = await db.get(Incident, incident_id)
    if not incident:
        raise HTTPException(404, f"Incident {incident_id} not found")
    if incident.status == IncidentStatus.analyzing:
        raise HTTPException(409, "Analysis already in progress")

    background_tasks.add_task(run_analysis, incident_id)
    return {"incident_id": incident_id, "status": "analysis_triggered"}


@router.post("", response_model=IncidentSummary, status_code=201)
async def create_incident(
    payload: IncidentCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    incident = Incident(
        title=payload.title,
        service_name=payload.service_name,
        severity=payload.severity,
        source=payload.source,
        alert_payload=payload.alert_payload,
        log_snippets=payload.log_snippets,
        metrics_data=payload.metrics_data,
        status=IncidentStatus.received,
    )
    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    background_tasks.add_task(run_analysis, incident.id)
    return incident
