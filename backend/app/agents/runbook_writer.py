import logging
import time

from app.agents.state import IncidentState
from app.services.ollama import ollama

logger = logging.getLogger(__name__)

RUNBOOK_PROMPT = """\
You are a senior SRE writing an incident runbook. Based on the analysis below, write a detailed, actionable runbook.

Service: {service}
Severity: {severity}
Root Cause: {root_cause}
Contributing Factors: {factors}

Format the runbook in Markdown with these sections:

## Immediate Actions (first 15 minutes)
Numbered steps to stabilize the system immediately.

## Investigation Steps
Numbered steps to verify the root cause and gather more information.

## Remediation
Numbered steps to fix the underlying issue.

## Verification
Steps to confirm the fix worked and the service is healthy.

## Prevention
3-5 action items to prevent this from happening again (include owners if determinable).

Be specific, use commands and examples where applicable. Target audience is an on-call engineer."""

SUMMARY_PROMPT = """\
You are an expert technical writer. Write a clear, concise incident summary for both engineers and customer success managers.

Incident Details:
- Service: {service}
- Severity: {severity}
- Alert: {title}
- Root Cause: {root_cause}
- Confidence: {confidence:.0%}
- Contributing Factors: {factors}

Write 3-4 sentences that explain:
1. What happened and which service was affected
2. The root cause in plain language
3. The current status and immediate impact
4. Next steps

Avoid jargon where possible. Be factual and direct."""


async def runbook_writer_node(state: IncidentState) -> IncidentState:
    start = time.monotonic()
    agent_name = "Runbook Writer"

    factors = ", ".join(state.get("contributing_factors", [])) or "None identified"

    try:
        runbook = await ollama.generate(
            RUNBOOK_PROMPT.format(
                service=state["service_name"],
                severity=state["severity"],
                root_cause=state.get("root_cause", "Unknown"),
                factors=factors,
            )
        )
    except Exception as e:
        logger.exception("Runbook generation failed")
        runbook = f"Runbook generation failed: {e}"

    try:
        summary = await ollama.generate(
            SUMMARY_PROMPT.format(
                service=state["service_name"],
                severity=state["severity"],
                title=state["title"],
                root_cause=state.get("root_cause", "Unknown"),
                confidence=state.get("confidence", 0.0),
                factors=factors,
            )
        )
    except Exception as e:
        logger.exception("Summary generation failed")
        summary = f"Summary generation failed: {e}"

    latency_ms = int((time.monotonic() - start) * 1000)
    logger.info("Runbook + summary generated in %dms", latency_ms)

    step = {
        "agent": agent_name,
        "input": f"Root cause: {state.get('root_cause', 'Unknown')}",
        "output": f"Generated runbook ({len(runbook)} chars) and summary ({len(summary)} chars)",
        "latency_ms": latency_ms,
        "status": "completed",
    }

    return {
        **state,
        "runbook": runbook,
        "summary": summary,
        "steps": [*state.get("steps", []), step],
    }
