"""
LangGraph QA Workflow — defines the multi-agent pipeline as a StateGraph.

The workflow follows this sequence:
START → supervisor_start → code_loader → code_analyzer → security_agent →
test_generator → test_runner → coverage_agent → bug_analysis →
root_cause → qa_report → supervisor_end → END
"""

from langgraph.graph import END, START, StateGraph

from backend.agents.bug_analysis import run_bug_analysis
from backend.agents.code_analyzer import run_code_analyzer
from backend.agents.code_loader import run_code_loader
from backend.agents.coverage_agent import run_coverage_agent
from backend.agents.qa_report import run_qa_report
from backend.agents.root_cause import run_root_cause
from backend.agents.security_agent import run_security_agent
from backend.agents.supervisor import run_supervisor_end, run_supervisor_start
from backend.agents.test_generator import run_test_generator
from backend.agents.test_runner import run_test_runner
from backend.models.state import QAState


def build_qa_graph() -> StateGraph:
    """
    Build and compile the LangGraph workflow for the AI QA Engineer.
    
    Each node is a specialized agent function that reads from and writes
    to the shared QAState TypedDict.
    """
    graph = StateGraph(QAState)

    # ── Register Nodes (Agents) ──────────────────────────────────────────────
    graph.add_node("supervisor_start", run_supervisor_start)
    graph.add_node("code_loader", run_code_loader)
    graph.add_node("code_analyzer", run_code_analyzer)
    graph.add_node("security_agent", run_security_agent)
    graph.add_node("test_generator", run_test_generator)
    graph.add_node("test_runner", run_test_runner)
    graph.add_node("coverage_agent", run_coverage_agent)
    graph.add_node("bug_analysis", run_bug_analysis)
    graph.add_node("root_cause", run_root_cause)
    graph.add_node("qa_report", run_qa_report)
    graph.add_node("supervisor_end", run_supervisor_end)

    # ── Define Edges (Sequential Flow) ──────────────────────────────────────
    graph.add_edge(START, "supervisor_start")
    graph.add_edge("supervisor_start", "code_loader")
    graph.add_edge("code_loader", "code_analyzer")
    graph.add_edge("code_analyzer", "security_agent")
    graph.add_edge("security_agent", "test_generator")
    graph.add_edge("test_generator", "test_runner")
    graph.add_edge("test_runner", "coverage_agent")
    graph.add_edge("coverage_agent", "bug_analysis")
    graph.add_edge("bug_analysis", "root_cause")
    graph.add_edge("root_cause", "qa_report")
    graph.add_edge("qa_report", "supervisor_end")
    graph.add_edge("supervisor_end", END)

    return graph.compile()


# Compiled graph singleton
_qa_graph = None


def get_qa_graph():
    """Get or build the compiled QA graph."""
    global _qa_graph
    if _qa_graph is None:
        _qa_graph = build_qa_graph()
    return _qa_graph
