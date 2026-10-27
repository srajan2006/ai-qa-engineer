"""
Security Agent — uses Bandit for deterministic security vulnerability scanning.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from backend.models.state import QAState


# Known dangerous patterns for fallback analysis
SECURITY_PATTERNS = [
    {
        "pattern": "subprocess",
        "code": "B603",
        "severity": "High",
        "description": "Subprocess call detected — verify no unsanitized input is used.",
        "recommendation": "Use subprocess with a list of arguments instead of shell=True.",
    },
    {
        "pattern": "shell=True",
        "code": "B602",
        "severity": "Critical",
        "description": "Subprocess with shell=True is vulnerable to command injection.",
        "recommendation": "Remove shell=True and pass arguments as a list.",
    },
    {
        "pattern": "eval(",
        "code": "B307",
        "severity": "Critical",
        "description": "Use of eval() with potentially untrusted input — arbitrary code execution.",
        "recommendation": "Replace eval() with safer alternatives (ast.literal_eval for literals).",
    },
    {
        "pattern": "exec(",
        "code": "B102",
        "severity": "Critical",
        "description": "Use of exec() is a security risk.",
        "recommendation": "Avoid exec(); refactor to use importlib or other safe mechanisms.",
    },
    {
        "pattern": "pickle.load",
        "code": "B301",
        "severity": "Critical",
        "description": "Pickle deserialization of untrusted data allows arbitrary code execution.",
        "recommendation": "Use JSON or other safe serialization formats.",
    },
    {
        "pattern": "hashlib.md5",
        "code": "B324",
        "severity": "High",
        "description": "MD5 is cryptographically broken and should not be used for security.",
        "recommendation": "Use hashlib.sha256 or bcrypt/argon2 for passwords.",
    },
    {
        "pattern": "SECRET_KEY",
        "code": "B105",
        "severity": "Critical",
        "description": "Possible hardcoded secret key detected in source code.",
        "recommendation": "Move secrets to environment variables or a secrets manager.",
    },
    {
        "pattern": "API_KEY",
        "code": "B105",
        "severity": "Critical",
        "description": "Possible hardcoded API key detected in source code.",
        "recommendation": "Use environment variables: os.getenv('API_KEY')",
    },
    {
        "pattern": "password",
        "code": "B106",
        "severity": "High",
        "description": "Possible hardcoded password in source code.",
        "recommendation": "Use environment variables or a vault for credential storage.",
    },
]


def run_security_agent(state: QAState) -> QAState:
    """
    Agent: Security Agent
    
    Responsibility: Detect security vulnerabilities using Bandit.
    Falls back to pattern-based detection if Bandit is unavailable.
    """
    logger.info("[Security Agent] Starting...")
    state["workflow_status"]["security_agent"] = "running"
    state["current_agent"] = "security_agent"

    try:
        source_files = state.get("source_files", {})
        project_path = state.get("project_path", "")

        if not source_files:
            raise ValueError("No source files to analyze.")

        findings = _run_bandit(project_path)

        if not findings:
            # Fallback: pattern-based scan
            logger.info("[Security Agent] Bandit unavailable — using pattern scan fallback.")
            findings = _pattern_scan(source_files)

        # Count by severity
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for f in findings:
            sev = f.get("severity", "Low")
            if sev in severity_counts:
                severity_counts[sev] += 1

        # Security score: start at 100, deduct per finding
        score = 100
        score -= severity_counts["Critical"] * 20
        score -= severity_counts["High"] * 10
        score -= severity_counts["Medium"] * 5
        score -= severity_counts["Low"] * 2
        score = max(score, 0)

        state["security_results"] = {
            "score": int(score),
            "findings": findings,
            "finding_count": len(findings),
            "severity_counts": severity_counts,
        }
        state["workflow_status"]["security_agent"] = "completed"
        logger.info(
            f"[Security Agent] Found {len(findings)} security issues. Score: {score}/100"
        )

    except Exception as e:
        logger.error(f"[Security Agent] Failed: {e}")
        state["workflow_status"]["security_agent"] = "failed"
        state["errors"] = state.get("errors", []) + [f"Security Agent: {str(e)}"]
        state["security_results"] = {
            "score": 50, "findings": [], "finding_count": 0,
            "severity_counts": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
        }

    return state


def _run_bandit(project_path: str) -> list[dict[str, Any]]:
    """Run Bandit security scanner."""
    findings = []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "bandit", "-r", project_path, "-f", "json", "-q"],
            capture_output=True, text=True, timeout=60
        )
        # Bandit exits with 1 if issues found, which is normal
        if result.stdout:
            data = json.loads(result.stdout)
            for issue in data.get("results", []):
                sev_map = {"HIGH": "Critical", "MEDIUM": "High", "LOW": "Medium"}
                conf_map = {"HIGH": "High", "MEDIUM": "Medium", "LOW": "Low"}
                findings.append({
                    "code": issue.get("test_id", ""),
                    "severity": sev_map.get(issue.get("issue_severity", "LOW"), "Low"),
                    "confidence": conf_map.get(issue.get("issue_confidence", "LOW"), "Low"),
                    "file": Path(issue.get("filename", "")).name,
                    "line": issue.get("line_number", 0),
                    "description": issue.get("issue_text", ""),
                    "recommendation": f"See Bandit rule {issue.get('test_id', '')} for remediation.",
                    "more_info": issue.get("more_info", ""),
                })
    except Exception as e:
        logger.debug(f"Bandit not available: {e}")
    return findings


def _pattern_scan(source_files: dict[str, str]) -> list[dict[str, Any]]:
    """Fallback pattern-based security scan."""
    findings = []
    for filename, source_code in source_files.items():
        lines = source_code.splitlines()
        for line_num, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for pattern_info in SECURITY_PATTERNS:
                pattern = pattern_info["pattern"]
                # For credential patterns, only match assignments
                if pattern in ("SECRET_KEY", "API_KEY", "password"):
                    if "=" in line and pattern.lower() in line.lower() and '"' in line:
                        findings.append({
                            "code": pattern_info["code"],
                            "severity": pattern_info["severity"],
                            "confidence": "High",
                            "file": filename,
                            "line": line_num,
                            "description": pattern_info["description"],
                            "recommendation": pattern_info["recommendation"],
                        })
                elif pattern in stripped:
                    findings.append({
                        "code": pattern_info["code"],
                        "severity": pattern_info["severity"],
                        "confidence": "High",
                        "file": filename,
                        "line": line_num,
                        "description": pattern_info["description"],
                        "recommendation": pattern_info["recommendation"],
                    })
    # Deduplicate
    seen = set()
    unique = []
    for f in findings:
        key = (f["file"], f["line"], f["code"])
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique
