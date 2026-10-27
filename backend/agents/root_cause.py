"""
Root Cause Analysis Agent — uses Gemini to perform deep root cause analysis
on each major/critical bug identified.
"""

import json
import re
from typing import Any

from loguru import logger

from backend.models.state import QAState
from backend.prompts.prompts import root_cause_prompt
from backend.services.gemini_service import get_gemini_service


def run_root_cause(state: QAState) -> QAState:
    """
    Agent: Root Cause Analysis
    
    Responsibility: For each critical/major bug, use Gemini to explain:
    - WHY the bug exists
    - What the actual root cause is
    - Business and technical impact
    - Suggested fix
    - Fix complexity
    """
    logger.info("[Root Cause Analysis] Starting...")
    state["workflow_status"]["root_cause"] = "running"
    state["current_agent"] = "root_cause"

    try:
        bug_reports = state.get("bug_reports", [])
        source_files = state.get("source_files", {})

        # Only do RCA for Critical and Major bugs to save time/tokens
        priority_bugs = [
            b for b in bug_reports
            if b.get("severity") in ("Critical", "Major")
        ]

        gemini = get_gemini_service()
        rca_results: list[dict[str, Any]] = []

        for bug in priority_bugs[:6]:  # Limit to avoid long processing
            # Get the relevant source file content
            bug_file = bug.get("file", "")
            source_code = source_files.get(bug_file, "")
            if not source_code:
                # Try to find by filename only (not path)
                for fname, code in source_files.items():
                    if bug_file in fname or fname.endswith(bug_file):
                        source_code = code
                        break

            prompt = root_cause_prompt(bug, source_code)
            logger.debug(f"[Root Cause] Analyzing {bug.get('bug_id')}...")

            raw = gemini.generate(prompt)
            rca = _parse_rca(raw, bug)
            rca["bug_id"] = bug.get("bug_id")
            rca["severity"] = bug.get("severity")
            rca["file"] = bug.get("file")
            rca["function"] = bug.get("function")
            rca_results.append(rca)

        state["root_cause_analysis"] = rca_results
        state["workflow_status"]["root_cause"] = "completed"
        logger.info(f"[Root Cause Analysis] Completed for {len(rca_results)} bugs.")

    except Exception as e:
        logger.error(f"[Root Cause Analysis] Failed: {e}")
        state["workflow_status"]["root_cause"] = "failed"
        state["errors"] = state.get("errors", []) + [f"Root Cause: {str(e)}"]
        state["root_cause_analysis"] = _fallback_rca(state.get("bug_reports", []))

    return state


def _parse_rca(raw: str, bug: dict) -> dict[str, Any]:
    """Parse Gemini's RCA JSON response."""
    raw = raw.strip()

    # Extract JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            rca = json.loads(match.group())
            if isinstance(rca, dict):
                return _validate_rca(rca)
        except json.JSONDecodeError:
            pass

    try:
        rca = json.loads(raw)
        if isinstance(rca, dict):
            return _validate_rca(rca)
    except json.JSONDecodeError:
        pass

    # Fallback for this specific bug
    return _fallback_single_rca(bug)


def _validate_rca(rca: dict) -> dict[str, Any]:
    """Ensure RCA has all required fields."""
    return {
        "root_cause": rca.get("root_cause", "Root cause analysis pending."),
        "affected_component": rca.get("affected_component", "Unknown"),
        "fix_suggestion": rca.get("fix_suggestion", "Review and fix the identified issue."),
        "fix_complexity": rca.get("fix_complexity", "Medium"),
        "confidence": int(rca.get("confidence", 75)),
        "business_impact": rca.get("business_impact", "May affect system stability."),
        "technical_impact": rca.get("technical_impact", "Requires code changes."),
    }


def _fallback_single_rca(bug: dict) -> dict[str, Any]:
    """Generate a deterministic RCA for known bug types."""
    desc = bug.get("description", "").lower()

    if "zero" in desc or "division" in desc:
        return {
            "root_cause": "The function performs division without first validating that the denominator is non-zero. This is a missing input validation guard clause.",
            "affected_component": f"{bug.get('file', '?')} → {bug.get('function', '?')}()",
            "fix_suggestion": "Add guard: `if b == 0: raise ValueError('Denominator cannot be zero')`",
            "fix_complexity": "Low",
            "confidence": 96,
            "business_impact": "Application crashes with unhandled exception when denominator is zero, causing service disruption.",
            "technical_impact": "Unhandled ZeroDivisionError propagates up the call stack, potentially terminating the process.",
        }
    elif "sql injection" in desc or "sql" in desc:
        return {
            "root_cause": "User-supplied input is directly interpolated into SQL query strings using f-strings or string formatting, bypassing parameterized query protection.",
            "affected_component": f"{bug.get('file', '?')} → {bug.get('function', '?')}()",
            "fix_suggestion": "Use parameterized queries: `cursor.execute('SELECT * FROM users WHERE username = ?', (username,))`",
            "fix_complexity": "Low",
            "confidence": 99,
            "business_impact": "Attackers can extract, modify, or delete entire database contents.",
            "technical_impact": "Complete database compromise; authentication bypass possible.",
        }
    elif "hardcoded" in desc or "secret" in desc or "api_key" in desc:
        return {
            "root_cause": "Credentials and secrets are defined as string literals in source code rather than being loaded from environment variables or a secrets manager.",
            "affected_component": f"{bug.get('file', '?')} → module level",
            "fix_suggestion": "Replace with: `SECRET_KEY = os.getenv('SECRET_KEY')` and add to .env file.",
            "fix_complexity": "Low",
            "confidence": 99,
            "business_impact": "If code is committed to version control, credentials are permanently exposed to anyone with repository access.",
            "technical_impact": "Credential leak; attacker can impersonate the service or access third-party APIs.",
        }
    else:
        return {
            "root_cause": f"The identified issue in {bug.get('function', 'the function')} stems from missing validation or error handling for edge-case inputs.",
            "affected_component": f"{bug.get('file', '?')} → {bug.get('function', '?')}()",
            "fix_suggestion": "Add appropriate input validation and error handling for all edge cases.",
            "fix_complexity": "Medium",
            "confidence": 80,
            "business_impact": "May cause unexpected behavior or errors in production.",
            "technical_impact": "Code robustness and reliability reduced.",
        }


def _fallback_rca(bug_reports: list[dict]) -> list[dict[str, Any]]:
    """Generate RCA for all critical/major bugs using fallback."""
    return [
        {**_fallback_single_rca(bug), "bug_id": bug.get("bug_id"), "severity": bug.get("severity"),
         "file": bug.get("file"), "function": bug.get("function")}
        for bug in bug_reports
        if bug.get("severity") in ("Critical", "Major")
    ]
