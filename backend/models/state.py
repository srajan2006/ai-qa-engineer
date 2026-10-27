"""
Shared LangGraph state model for the AI QA Engineer pipeline.
Each agent reads from and writes to this TypedDict.
"""

from typing import Any, Optional, TypedDict


class QAState(TypedDict, total=False):
    """Shared state passed between all agents in the LangGraph workflow."""

    # Input
    project_path: str
    job_id: str

    # Code Loader output
    project_info: dict[str, Any]
    source_files: dict[str, str]          # filename -> source code
    project_structure: list[str]

    # Code Analyzer output
    code_quality_results: dict[str, Any]  # ruff findings + AST metrics

    # Security Agent output
    security_results: dict[str, Any]      # bandit findings

    # Test Generator output
    test_cases: str                        # generated pytest code as string
    test_file_path: str                    # path where tests were written

    # Test Runner output
    test_results: dict[str, Any]           # pytest results

    # Coverage Agent output
    coverage_results: dict[str, Any]       # coverage %

    # Bug Analysis output
    bug_reports: list[dict[str, Any]]      # list of bugs

    # Root Cause Analysis output
    root_cause_analysis: list[dict[str, Any]]

    # QA Report Agent output
    qa_report: dict[str, Any]

    # Suggested fixes
    suggested_fixes: list[dict[str, Any]]

    # Workflow control
    workflow_status: dict[str, str]        # agent_name -> "pending"|"running"|"completed"|"failed"
    current_agent: str
    errors: list[str]

    # Human approval
    approval_status: str                   # "pending"|"approved"|"rejected"
    approval_notes: str


def create_initial_state(project_path: str, job_id: str) -> QAState:
    """Create a fresh initial state for a new analysis job."""
    return QAState(
        project_path=project_path,
        job_id=job_id,
        project_info={},
        source_files={},
        project_structure=[],
        code_quality_results={},
        security_results={},
        test_cases="",
        test_file_path="",
        test_results={},
        coverage_results={},
        bug_reports=[],
        root_cause_analysis=[],
        qa_report={},
        suggested_fixes=[],
        workflow_status={
            "code_loader": "pending",
            "code_analyzer": "pending",
            "security_agent": "pending",
            "test_generator": "pending",
            "test_runner": "pending",
            "coverage_agent": "pending",
            "bug_analysis": "pending",
            "root_cause": "pending",
            "qa_report": "pending",
        },
        current_agent="",
        errors=[],
        approval_status="pending",
        approval_notes="",
    )
