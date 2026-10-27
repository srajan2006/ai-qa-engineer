"""
Supervisor Agent — orchestrates the entire QA workflow via LangGraph.
"""

from loguru import logger

from backend.models.state import QAState


def run_supervisor_start(state: QAState) -> QAState:
    """
    Supervisor: Initialization step.
    Sets up the workflow and validates inputs before dispatching agents.
    """
    logger.info(f"[Supervisor] QA workflow started for job: {state.get('job_id')}")
    logger.info(f"[Supervisor] Project: {state.get('project_path')}")
    state["current_agent"] = "supervisor"
    return state


def run_supervisor_end(state: QAState) -> QAState:
    """
    Supervisor: Final step — validate all agents completed and summarize.
    """
    workflow_status = state.get("workflow_status", {})
    errors = state.get("errors", [])

    completed = [k for k, v in workflow_status.items() if v == "completed"]
    failed = [k for k, v in workflow_status.items() if v == "failed"]

    logger.info(f"[Supervisor] Workflow complete.")
    logger.info(f"[Supervisor] Completed agents: {completed}")
    if failed:
        logger.warning(f"[Supervisor] Failed agents: {failed}")
    if errors:
        logger.warning(f"[Supervisor] Errors encountered: {errors}")

    state["current_agent"] = "completed"
    return state
