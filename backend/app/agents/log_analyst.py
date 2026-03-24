import logging
import time

from app.agents.state import IncidentState
from app.services.ollama import ollama

logger = logging.getLogger(__name__)

PROMPT = """\
You are an expert SRE log analyst. Analyze the following log snippets from a production incident.

Service: {service}
Severity: {severity}
Logs:
{logs}

Provide a structured analysis covering:
1. Error type and classification
2. Affected components or services
3. Timeline of events (earliest to latest)
4. Error frequency and patterns
5. Any stack traces or root signals visible in the logs

Be concise and technical. Focus on actionable findings."""


async def log_analyst_node(state: IncidentState) -> IncidentState:
    start = time.monotonic()
    agent_name = "Log Analyst"
    logs = state.get("log_snippets", [])

    if not logs:
        result = "No log snippets provided. Unable to perform log analysis."
        latency_ms = 0
    else:
        log_text = "\n".join(f"[{i+1}] {line}" for i, line in enumerate(logs))
        prompt = PROMPT.format(
            service=state["service_name"],
            severity=state["severity"],
            logs=log_text,
        )
        try:
            result = await ollama.generate(prompt)
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info("Log analyst completed in %dms", latency_ms)
        except Exception as e:
            logger.exception("Log analyst failed")
            result = f"Log analysis failed: {e}"
            latency_ms = int((time.monotonic() - start) * 1000)

    step = {
        "agent": agent_name,
        "input": f"{len(logs)} log snippets from {state['service_name']}",
        "output": result,
        "latency_ms": latency_ms,
        "status": "completed" if "failed" not in result.lower()[:20] else "failed",
    }

    return {
        **state,
        "log_analysis": result,
        "steps": [*state.get("steps", []), step],
    }
