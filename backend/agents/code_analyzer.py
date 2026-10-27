"""
Code Analyzer Agent — uses Ruff for linting and AST for complexity metrics.
Deterministic analysis: no LLM involved.
"""

import ast
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from loguru import logger

from backend.models.state import QAState


def run_code_analyzer(state: QAState) -> QAState:
    """
    Agent: Code Analyzer
    
    Responsibility: Analyze code quality using Ruff (linting) and AST
    (complexity, function count, etc.). Pure deterministic analysis.
    """
    logger.info("[Code Analyzer] Starting...")
    state["workflow_status"]["code_analyzer"] = "running"
    state["current_agent"] = "code_analyzer"

    try:
        source_files = state.get("source_files", {})
        if not source_files:
            raise ValueError("No source files to analyze.")

        all_issues: list[dict] = []
        ast_metrics: dict[str, Any] = {}
        total_functions = 0
        total_classes = 0
        total_complexity = 0

        # ── 1. AST Metrics ──────────────────────────────────────────────────
        for filename, source_code in source_files.items():
            try:
                tree = ast.parse(source_code, filename=filename)
                metrics = _analyze_ast(tree, filename)
                ast_metrics[filename] = metrics
                total_functions += metrics["functions"]
                total_classes += metrics["classes"]
                total_complexity += metrics["complexity"]
            except SyntaxError as e:
                logger.warning(f"[Code Analyzer] Syntax error in {filename}: {e}")
                ast_metrics[filename] = {"error": str(e)}

        # ── 2. Ruff Linting ─────────────────────────────────────────────────
        ruff_issues = _run_ruff(source_files, state.get("project_path", ""))

        # ── 3. Aggregate Results ─────────────────────────────────────────────
        file_count = len(source_files)
        avg_complexity = total_complexity / file_count if file_count > 0 else 0

        # Score: start at 100, deduct for issues
        score = 100
        score -= min(len(ruff_issues) * 2, 30)   # up to -30 for linting issues
        score -= min(max(0, avg_complexity - 5) * 2, 20)  # up to -20 for complexity
        score = max(score, 10)

        state["code_quality_results"] = {
            "score": int(score),
            "issues": ruff_issues,
            "issue_count": len(ruff_issues),
            "ast_metrics": ast_metrics,
            "summary": {
                "total_functions": total_functions,
                "total_classes": total_classes,
                "avg_complexity": round(avg_complexity, 2),
                "files_analyzed": file_count,
            },
        }
        state["workflow_status"]["code_analyzer"] = "completed"
        logger.info(
            f"[Code Analyzer] Found {len(ruff_issues)} issues. Score: {score}/100"
        )

    except Exception as e:
        logger.error(f"[Code Analyzer] Failed: {e}")
        state["workflow_status"]["code_analyzer"] = "failed"
        state["errors"] = state.get("errors", []) + [f"Code Analyzer: {str(e)}"]
        state["code_quality_results"] = {"score": 50, "issues": [], "issue_count": 0, "ast_metrics": {}}

    return state


def _analyze_ast(tree: ast.AST, filename: str) -> dict[str, Any]:
    """Extract metrics from an AST."""
    functions = 0
    classes = 0
    complexity = 1  # base complexity
    docstrings_missing = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            # Simple complexity: count branches
            for child in ast.walk(node):
                if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                                       ast.With, ast.Assert, ast.BoolOp)):
                    complexity += 1
            # Check for missing docstring
            if not (node.body and isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant)):
                docstrings_missing += 1

        elif isinstance(node, ast.ClassDef):
            classes += 1

    return {
        "functions": functions,
        "classes": classes,
        "complexity": complexity,
        "docstrings_missing": docstrings_missing,
    }


def _run_ruff(source_files: dict[str, str], project_path: str) -> list[dict]:
    """Run Ruff linter on the project. Falls back to manual checks if Ruff unavailable."""
    issues = []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--output-format=json", project_path],
            capture_output=True, text=True, timeout=30
        )
        if result.stdout:
            raw = json.loads(result.stdout)
            for item in raw:
                # Make path relative-looking for display
                fname = Path(item.get("filename", "")).name
                issues.append({
                    "file": fname,
                    "line": item.get("location", {}).get("row", 0),
                    "column": item.get("location", {}).get("column", 0),
                    "code": item.get("code", ""),
                    "message": item.get("message", ""),
                    "severity": _ruff_severity(item.get("code", "")),
                })
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError, Exception) as e:
        logger.warning(f"[Code Analyzer] Ruff not available or failed: {e}. Using fallback.")
        issues = _fallback_analysis(source_files)

    return issues


def _ruff_severity(code: str) -> str:
    """Map Ruff rule codes to severity levels."""
    if code.startswith(("E1", "E2", "E7", "W6")):
        return "major"
    elif code.startswith(("F", "B", "S")):
        return "major"
    else:
        return "minor"


def _fallback_analysis(source_files: dict[str, str]) -> list[dict]:
    """Basic code smell detection when Ruff is unavailable."""
    issues = []
    bad_patterns = [
        ("print(", "T201", "Found `print` statement - use logging instead"),
        ("except:", "E722", "Bare `except` clause without exception type"),
        ("import *", "F403", "Wildcard import - use explicit imports"),
        ("eval(", "S307", "Use of `eval` detected - security risk"),
        ("exec(", "S102", "Use of `exec` detected - security risk"),
        ("shell=True", "S603", "Subprocess with shell=True - security risk"),
    ]
    for filename, source_code in source_files.items():
        lines = source_code.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for pattern, code, message in bad_patterns:
                if pattern in line and not line.strip().startswith("#"):
                    issues.append({
                        "file": filename,
                        "line": line_num,
                        "column": line.index(pattern) + 1,
                        "code": code,
                        "message": message,
                        "severity": "major",
                    })
    return issues
