"""
Code Loader Agent — scans a project directory, loads Python source files,
and extracts project metadata.
"""

import os
from pathlib import Path
from typing import Any

from loguru import logger

from backend.models.state import QAState


def run_code_loader(state: QAState) -> QAState:
    """
    Agent: Code Loader
    
    Responsibility: Scan the project directory, load all Python files,
    build the project structure tree, and populate state with source code.
    """
    logger.info("[Code Loader] Starting...")
    state["workflow_status"]["code_loader"] = "running"
    state["current_agent"] = "code_loader"

    try:
        project_path = Path(state["project_path"])

        if not project_path.exists():
            raise FileNotFoundError(f"Project path does not exist: {project_path}")

        if not project_path.is_dir():
            raise ValueError(f"Project path is not a directory: {project_path}")

        # Scan for Python files
        python_files = list(project_path.rglob("*.py"))

        if not python_files:
            raise ValueError("No Python files found in the project directory.")

        # Load source files
        source_files: dict[str, str] = {}
        project_structure: list[str] = []
        total_lines = 0

        for py_file in python_files:
            # Skip __pycache__ and .venv directories
            parts = py_file.parts
            if any(p in ("__pycache__", ".venv", "venv", "node_modules", ".git") for p in parts):
                continue

            try:
                rel_path = py_file.relative_to(project_path)
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                source_files[str(rel_path)] = content
                project_structure.append(str(rel_path))
                total_lines += len(content.splitlines())
            except Exception as e:
                logger.warning(f"[Code Loader] Could not read {py_file}: {e}")

        project_info: dict[str, Any] = {
            "name": project_path.name,
            "path": str(project_path),
            "file_count": len(source_files),
            "total_lines": total_lines,
            "python_files": sorted(project_structure),
        }

        state["project_info"] = project_info
        state["source_files"] = source_files
        state["project_structure"] = sorted(project_structure)
        state["workflow_status"]["code_loader"] = "completed"

        logger.info(
            f"[Code Loader] Loaded {len(source_files)} files, "
            f"{total_lines} total lines."
        )

    except Exception as e:
        logger.error(f"[Code Loader] Failed: {e}")
        state["workflow_status"]["code_loader"] = "failed"
        state["errors"] = state.get("errors", []) + [f"Code Loader: {str(e)}"]

    return state
