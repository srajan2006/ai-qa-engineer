"""
QA Report Agent — aggregates all analysis results into a final professional report.
Uses Gemini for the executive narrative summary.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from loguru import logger

from backend.config import REPORTS_DIR
from backend.models.state import QAState
from backend.prompts.prompts import qa_report_prompt
from backend.services.gemini_service import get_gemini_service


def run_qa_report(state: QAState) -> QAState:
    """
    Agent: QA Report
    
    Responsibility: Combine all analysis results into a structured report.
    Calculate overall quality scores. Generate an AI executive summary.
    Save report as JSON and HTML.
    """
    logger.info("[QA Report] Generating final report...")
    state["workflow_status"]["qa_report"] = "running"
    state["current_agent"] = "qa_report"

    try:
        # ── Gather all results ───────────────────────────────────────────────
        project_info = state.get("project_info", {})
        code_quality = state.get("code_quality_results", {})
        security = state.get("security_results", {})
        test_results = state.get("test_results", {})
        coverage = state.get("coverage_results", {})
        bug_reports = state.get("bug_reports", [])
        rca = state.get("root_cause_analysis", [])

        # ── Calculate Scores ─────────────────────────────────────────────────
        quality_score = _calculate_quality_score(code_quality, test_results, coverage, bug_reports)
        security_score = security.get("score", 70)
        test_pass_rate = test_results.get("pass_rate", 0.0)
        total_coverage = coverage.get("total_coverage", 0.0)

        # Bug counts by severity
        critical_bugs = [b for b in bug_reports if b.get("severity") == "Critical"]
        major_bugs = [b for b in bug_reports if b.get("severity") == "Major"]
        minor_bugs = [b for b in bug_reports if b.get("severity") == "Minor"]

        # Security findings by severity
        sec_findings = security.get("findings", [])
        sec_severity = security.get("severity_counts", {})

        # ── AI Narrative ─────────────────────────────────────────────────────
        gemini = get_gemini_service()
        prompt = qa_report_prompt(
            project_info=project_info,
            quality_score=quality_score,
            security_score=security_score,
            test_pass_rate=test_pass_rate,
            coverage=total_coverage,
            bug_count=len(bug_reports),
            critical_count=len(critical_bugs),
            major_count=len(major_bugs),
            minor_count=len(minor_bugs),
        )
        executive_summary = gemini.generate(prompt)

        # ── Build Report ─────────────────────────────────────────────────────
        report: dict[str, Any] = {
            "report_id": state.get("job_id", "unknown"),
            "generated_at": datetime.now().isoformat(),
            "project": {
                "name": project_info.get("name", "Unknown"),
                "path": project_info.get("path", ""),
                "files": project_info.get("file_count", 0),
                "total_lines": project_info.get("total_lines", 0),
            },
            "scores": {
                "quality": quality_score,
                "security": security_score,
                "test_pass_rate": test_pass_rate,
                "coverage": total_coverage,
            },
            "summary": {
                "total_bugs": len(bug_reports),
                "critical": len(critical_bugs),
                "major": len(major_bugs),
                "minor": len(minor_bugs),
                "tests_passed": test_results.get("passed", 0),
                "tests_failed": test_results.get("failed", 0),
                "tests_total": test_results.get("total", 0),
            },
            "code_quality": {
                "score": code_quality.get("score", 0),
                "issue_count": code_quality.get("issue_count", 0),
                "issues": code_quality.get("issues", [])[:20],
                "ast_metrics": code_quality.get("summary", {}),
            },
            "security": {
                "score": security_score,
                "critical": sec_severity.get("Critical", 0),
                "high": sec_severity.get("High", 0),
                "medium": sec_severity.get("Medium", 0),
                "low": sec_severity.get("Low", 0),
                "findings": sec_findings[:20],
            },
            "test_results": {
                "passed": test_results.get("passed", 0),
                "failed": test_results.get("failed", 0),
                "total": test_results.get("total", 0),
                "pass_rate": test_pass_rate,
                "failed_tests": test_results.get("failed_tests", [])[:10],
            },
            "coverage": {
                "total": total_coverage,
                "lines_covered": coverage.get("lines_covered", 0),
                "lines_total": coverage.get("lines_total", 0),
                "by_file": coverage.get("file_coverage", {}),
            },
            "bugs": bug_reports,
            "root_cause_analysis": rca,
            "test_cases_generated": state.get("test_cases", ""),
            "executive_summary": executive_summary,
            "recommendations": _build_recommendations(
                quality_score, security_score, test_pass_rate, total_coverage,
                critical_bugs, major_bugs
            ),
            "approval_status": state.get("approval_status", "pending"),
        }

        # ── Save Report ───────────────────────────────────────────────────────
        job_id = state.get("job_id", "unknown")
        json_path = REPORTS_DIR / f"report_{job_id}.json"
        json_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

        state["qa_report"] = report
        state["workflow_status"]["qa_report"] = "completed"
        logger.info(
            f"[QA Report] Report generated. Quality: {quality_score}/100, "
            f"Security: {security_score}/100. Saved to {json_path}"
        )

    except Exception as e:
        logger.error(f"[QA Report] Failed: {e}")
        state["workflow_status"]["qa_report"] = "failed"
        state["errors"] = state.get("errors", []) + [f"QA Report: {str(e)}"]
        state["qa_report"] = {"error": str(e), "scores": {"quality": 0}}

    return state


def _calculate_quality_score(
    code_quality: dict, test_results: dict, coverage: dict, bugs: list
) -> int:
    """Calculate an overall quality score (0–100) from all metrics."""
    score = 100.0

    # Code quality contribution (weight: 30%)
    cq_score = code_quality.get("score", 70)
    score = score * 0.7 + cq_score * 0.3

    # Test pass rate (weight: 25%)
    pass_rate = test_results.get("pass_rate", 0.0)
    score -= (100 - pass_rate) * 0.25

    # Coverage (weight: 20%)
    cov = coverage.get("total_coverage", 0.0)
    if cov < 80:
        score -= (80 - cov) * 0.2

    # Bug severity (weight: 25%)
    critical = sum(1 for b in bugs if b.get("severity") == "Critical")
    major = sum(1 for b in bugs if b.get("severity") == "Major")
    minor = sum(1 for b in bugs if b.get("severity") == "Minor")
    score -= critical * 8
    score -= major * 4
    score -= minor * 1

    return max(0, min(100, int(score)))


def _build_recommendations(
    quality: int, security: int, pass_rate: float, coverage: float,
    critical_bugs: list, major_bugs: list
) -> list[str]:
    """Generate prioritized recommendations."""
    recs = []

    if critical_bugs:
        recs.append(
            f"🔴 URGENT: Fix {len(critical_bugs)} critical bug(s) before any deployment. "
            "These include security vulnerabilities and runtime errors."
        )

    if security < 70:
        recs.append(
            "🔐 Security: Remove all hardcoded credentials and use environment variables. "
            "Apply parameterized SQL queries to prevent injection attacks."
        )

    if major_bugs:
        recs.append(
            f"🟡 Resolve {len(major_bugs)} major bug(s) to prevent production incidents. "
            "Add input validation for all edge cases."
        )

    if coverage < 70:
        recs.append(
            f"📊 Increase test coverage from {coverage:.0f}% to at least 80%. "
            "Focus on untested functions in high-risk modules."
        )

    if pass_rate < 80:
        recs.append(
            f"🧪 Improve test pass rate from {pass_rate:.0f}% by fixing failing tests "
            "and correcting the underlying code defects."
        )

    if quality < 70:
        recs.append(
            "✨ Refactor code to improve maintainability: improve naming conventions, "
            "add missing docstrings, and handle exceptions properly."
        )

    recs.append("🔄 Implement CI/CD pipeline to run these checks automatically on every commit.")
    recs.append("📝 Add pre-commit hooks with Ruff and Bandit for early issue detection.")

    return recs
