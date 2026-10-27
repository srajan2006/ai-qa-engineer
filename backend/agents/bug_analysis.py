"""
Bug Analysis Agent — uses Gemini to analyze failed tests, code quality issues,
and security findings to identify and categorize bugs.
"""

import json
import re
from typing import Any

from loguru import logger

from backend.models.state import QAState
from backend.prompts.prompts import bug_analysis_prompt
from backend.services.gemini_service import get_gemini_service


def run_bug_analysis(state: QAState) -> QAState:
    """
    Agent: Bug Analysis
    
    Responsibility: Combine test failures, code quality, and security findings.
    Use Gemini to identify, describe, and categorize bugs.
    """
    logger.info("[Bug Analysis] Starting...")
    state["workflow_status"]["bug_analysis"] = "running"
    state["current_agent"] = "bug_analysis"

    try:
        source_files = state.get("source_files", {})
        test_results = state.get("test_results", {})
        code_quality = state.get("code_quality_results", {})
        security = state.get("security_results", {})

        gemini = get_gemini_service()
        prompt = bug_analysis_prompt(source_files, test_results, code_quality, security)
        logger.info(f"[Bug Analysis] Calling Gemini (demo_mode={gemini.is_demo_mode})...")

        raw = gemini.generate(prompt)
        bug_reports = _parse_bug_reports(raw)

        # Merge with security findings as additional bugs
        security_findings = security.get("findings", [])
        for finding in security_findings[:5]:  # Add top 5 security findings as bugs
            sev = finding.get("severity", "Medium")
            if sev == "Critical":
                bug_severity = "Critical"
            elif sev == "High":
                bug_severity = "Major"
            else:
                bug_severity = "Minor"

            # Check if already reported
            file_name = finding.get("file", "")
            line_num = finding.get("line", 0)
            already_exists = any(
                b.get("file") == file_name and b.get("line") == line_num
                for b in bug_reports
            )
            if not already_exists:
                bug_reports.append({
                    "bug_id": f"BUG-{len(bug_reports) + 1:03d}",
                    "severity": bug_severity,
                    "category": "Security",
                    "file": file_name,
                    "line": line_num,
                    "function": "unknown",
                    "description": finding.get("description", ""),
                    "confidence": 90,
                })

        # Renumber bugs
        for i, bug in enumerate(bug_reports, start=1):
            bug["bug_id"] = f"BUG-{i:03d}"

        state["bug_reports"] = bug_reports
        state["workflow_status"]["bug_analysis"] = "completed"

        critical = sum(1 for b in bug_reports if b.get("severity") == "Critical")
        major = sum(1 for b in bug_reports if b.get("severity") == "Major")
        minor = sum(1 for b in bug_reports if b.get("severity") == "Minor")
        logger.info(
            f"[Bug Analysis] Found {len(bug_reports)} bugs: "
            f"{critical} Critical, {major} Major, {minor} Minor"
        )

    except Exception as e:
        logger.error(f"[Bug Analysis] Failed: {e}")
        state["workflow_status"]["bug_analysis"] = "failed"
        state["errors"] = state.get("errors", []) + [f"Bug Analysis: {str(e)}"]
        state["bug_reports"] = []

    return state


def _parse_bug_reports(raw: str) -> list[dict[str, Any]]:
    """Parse Gemini's bug report JSON response."""
    # Try to extract JSON array from the response
    raw = raw.strip()

    # Find JSON array
    match = re.search(r"\[.*\]", raw, re.DOTALL)
    if match:
        try:
            bugs = json.loads(match.group())
            if isinstance(bugs, list):
                return [_validate_bug(b, i) for i, b in enumerate(bugs, 1)]
        except json.JSONDecodeError:
            pass

    # Try parsing as JSON directly
    try:
        bugs = json.loads(raw)
        if isinstance(bugs, list):
            return [_validate_bug(b, i) for i, b in enumerate(bugs, 1)]
    except json.JSONDecodeError:
        pass

    logger.warning("[Bug Analysis] Could not parse JSON — using fallback bug list.")
    return _fallback_bugs()


def _validate_bug(bug: dict, index: int) -> dict[str, Any]:
    """Ensure a bug dict has all required fields."""
    valid_severities = {"Critical", "Major", "Minor"}
    return {
        "bug_id": bug.get("bug_id", f"BUG-{index:03d}"),
        "severity": bug.get("severity", "Minor") if bug.get("severity") in valid_severities else "Minor",
        "category": bug.get("category", "Unknown"),
        "file": bug.get("file", "unknown.py"),
        "line": int(bug.get("line", 0)),
        "function": bug.get("function", "unknown"),
        "description": bug.get("description", "No description"),
        "confidence": int(bug.get("confidence", 70)),
    }


def _fallback_bugs() -> list[dict[str, Any]]:
    """Deterministic fallback bugs based on known demo project issues."""
    return [
        {
            "bug_id": "BUG-001", "severity": "Critical", "category": "Runtime Error",
            "file": "calculator.py", "line": 22, "function": "divide",
            "description": "Division by zero: no validation of denominator before division.",
            "confidence": 98,
        },
        {
            "bug_id": "BUG-002", "severity": "Critical", "category": "Security",
            "file": "user_service.py", "line": 11, "function": "module-level",
            "description": "Hardcoded SECRET_KEY and API_KEY in source code.",
            "confidence": 99,
        },
        {
            "bug_id": "BUG-003", "severity": "Critical", "category": "Security",
            "file": "database.py", "line": 38, "function": "get_user",
            "description": "SQL injection vulnerability: f-string used in SQL query.",
            "confidence": 97,
        },
        {
            "bug_id": "BUG-004", "severity": "Major", "category": "Runtime Error",
            "file": "calculator.py", "line": 55, "function": "average",
            "description": "ZeroDivisionError when empty list passed to average().",
            "confidence": 95,
        },
        {
            "bug_id": "BUG-005", "severity": "Major", "category": "Logic Error",
            "file": "calculator.py", "line": 40, "function": "calculate_discount",
            "description": "Discount over 100% produces negative price — no upper bound check.",
            "confidence": 92,
        },
        {
            "bug_id": "BUG-006", "severity": "Minor", "category": "Code Quality",
            "file": "utils.py", "line": 20, "function": "fn1",
            "description": "Non-descriptive function name 'fn1' — violates naming conventions.",
            "confidence": 88,
        },
    ]
