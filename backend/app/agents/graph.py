import logging

from langgraph.graph import END, StateGraph

from app.agents.log_analyst import log_analyst_node
from app.agents.metrics_correlator import metrics_correlator_node
from app.agents.root_cause import root_cause_node
from app.agents.runbook_writer import runbook_writer_node
from app.agents.state import IncidentState

logger = logging.getLogger(__name__)


def build_graph() -> StateGraph:
    graph = StateGraph(IncidentState)

    graph.add_node("log_analyst", log_analyst_node)
    graph.add_node("metrics_correlator", metrics_correlator_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("runbook_writer", runbook_writer_node)

    graph.set_entry_point("log_analyst")
    graph.add_edge("log_analyst", "metrics_correlator")
    graph.add_edge("metrics_correlator", "root_cause")
    graph.add_edge("root_cause", "runbook_writer")
    graph.add_edge("runbook_writer", END)

    return graph.compile()


incident_graph = build_graph()
