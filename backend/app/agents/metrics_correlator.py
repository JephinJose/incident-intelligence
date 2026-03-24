import json
import logging
import time

from app.agents.state import IncidentState
from app.services.ollama import ollama

logger = logging.getLogger(__name__)

PROMPT = """\
You are an expert SRE metrics analyst. Analyze the following infrastructure metrics from a production incident.

Service: {service}
Severity: {severity}
Alert: {title}
Metrics Data:
{metrics}

Log Analysis Context:
{log_analysis}

Provide a structured analysis covering:
1. Anomalies detected (CPU, memory, latency, error rates, etc.)
2. Correlation between different metrics
3. Blast radius — which services/endpoints are affected
4. Resource saturation points
5. Whether this is a traffic spike, resource leak, dependency failure, or configuration issue

Be specific with numbers where available. Focus on correlations that indicate cause vs. effect."""


async def metrics_correlator_node(state: IncidentState) -> IncidentState:
    start = time.monotonic()
    agent_name = "Metrics Correlator"
    metrics = state.get("metrics_data", {})

    if not metrics:
        result = "No metrics data provided. Analysis based on log context only."
        latency_ms = 0
    else:
        metrics_text = json.dumps(metrics, indent=2)
        prompt = PROMPT.format(
            service=state["service_name"],
            severity=state["severity"],
            title=state["title"],
            metrics=metrics_text,
            log_analysis=state.get("log_analysis", "Not available"),
        )
        try:
            result = await ollama.generate(prompt)
            latency_ms = int((time.monotonic() - start) * 1000)
            logger.info("Metrics correlator completed in %dms", latency_ms)
        except Exception as e:
            logger.exception("Metrics correlator failed")
            result = f"Metrics analysis failed: {e}"
            latency_ms = int((time.monotonic() - start) * 1000)

    step = {
        "agent": agent_name,
        "input": f"Metrics for {state['service_name']}: {list(metrics.keys())}",
        "output": result,
        "latency_ms": latency_ms,
        "status": "completed",
    }

    return {
        **state,
        "metrics_analysis": result,
        "steps": [*state.get("steps", []), step],
    }
