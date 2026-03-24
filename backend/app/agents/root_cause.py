import logging
import time

from app.agents.state import IncidentState
from app.services.ollama import ollama

logger = logging.getLogger(__name__)

PROMPT = """\
You are a senior SRE performing root cause analysis. Synthesize the following findings from a production incident.

Service: {service}
Severity: {severity}
Alert: {title}

Log Analysis:
{log_analysis}

Metrics Analysis:
{metrics_analysis}

Based on all evidence, provide:
1. PRIMARY ROOT CAUSE: A single, precise statement of the most likely root cause
2. CONFIDENCE: A percentage (0-100) indicating your confidence level
3. CONTRIBUTING FACTORS: Up to 3 secondary factors that worsened the incident
4. EVIDENCE: Key pieces of evidence supporting this conclusion
5. ALTERNATIVE HYPOTHESES: Any other possible root causes with brief reasoning for why they are less likely

Return your analysis as JSON with this exact structure:
{{
  "root_cause": "string",
  "confidence": 0.0,
  "contributing_factors": ["factor1", "factor2"],
  "evidence": ["evidence1", "evidence2"],
  "alternative_hypotheses": ["alt1", "alt2"]
}}"""


async def root_cause_node(state: IncidentState) -> IncidentState:
    start = time.monotonic()
    agent_name = "Root Cause Investigator"

    prompt = PROMPT.format(
        service=state["service_name"],
        severity=state["severity"],
        title=state["title"],
        log_analysis=state.get("log_analysis", "Not available"),
        metrics_analysis=state.get("metrics_analysis", "Not available"),
    )

    try:
        result = await ollama.generate_json(
            prompt,
            fallback={
                "root_cause": "Unable to determine root cause automatically",
                "confidence": 0.0,
                "contributing_factors": [],
                "evidence": [],
                "alternative_hypotheses": [],
            },
        )
        latency_ms = int((time.monotonic() - start) * 1000)
        logger.info("Root cause analysis completed in %dms", latency_ms)
    except Exception as e:
        logger.exception("Root cause analysis failed")
        result = {
            "root_cause": f"Analysis failed: {e}",
            "confidence": 0.0,
            "contributing_factors": [],
            "evidence": [],
            "alternative_hypotheses": [],
        }
        latency_ms = int((time.monotonic() - start) * 1000)

    root_cause_text = result.get("root_cause", "Unknown")
    confidence = float(result.get("confidence", 0.0))
    if confidence > 1.0:
        confidence = confidence / 100.0
    contributing_factors = result.get("contributing_factors", [])

    step = {
        "agent": agent_name,
        "input": "Log + metrics analysis synthesis",
        "output": f"Root cause: {root_cause_text} (confidence: {confidence:.0%})\nFactors: {', '.join(contributing_factors)}",
        "latency_ms": latency_ms,
        "status": "completed",
    }

    return {
        **state,
        "root_cause": root_cause_text,
        "confidence": confidence,
        "contributing_factors": contributing_factors,
        "steps": [*state.get("steps", []), step],
    }
