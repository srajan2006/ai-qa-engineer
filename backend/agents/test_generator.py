"""
Test Generator Agent — uses Gemini to generate pytest test cases
based on the analyzed source code.
"""

import re
from pathlib import Path

from loguru import logger

from backend.models.state import QAState
from backend.prompts.prompts import test_generation_prompt
from backend.services.gemini_service import get_gemini_service


def run_test_generator(state: QAState) -> QAState:
    """
    Agent: Test Generator
    
    Responsibility: Use Gemini LLM to generate meaningful pytest test cases
    for the analyzed source files.
    """
    logger.info("[Test Generator] Starting...")
    state["workflow_status"]["test_generator"] = "running"
    state["current_agent"] = "test_generator"

    try:
        source_files = state.get("source_files", {})
        if not source_files:
            raise ValueError("No source files to generate tests for.")

        # Focus on non-test files for generation
        non_test_files = {
            fname: code
            for fname, code in source_files.items()
            if not fname.startswith("test_") and not "test_" in Path(fname).name
        }

        if not non_test_files:
            non_test_files = source_files

        # Limit to avoid exceeding token limits
        # Prioritize smaller files (more focused tests)
        sorted_files = sorted(non_test_files.items(), key=lambda x: len(x[1]))[:5]
        selected_files = dict(sorted_files)

        gemini = get_gemini_service()
        prompt = test_generation_prompt(selected_files)
        logger.info(f"[Test Generator] Calling Gemini (demo_mode={gemini.is_demo_mode})...")

        raw_response = gemini.generate(prompt)
        test_code = _extract_python_code(raw_response)

        # Write test file to the project directory
        project_path = Path(state.get("project_path", "."))
        test_file_path = project_path / "test_ai_generated.py"

        test_file_path.write_text(test_code, encoding="utf-8")

        state["test_cases"] = test_code
        state["test_file_path"] = str(test_file_path)
        state["workflow_status"]["test_generator"] = "completed"

        logger.info(
            f"[Test Generator] Generated {_count_test_functions(test_code)} test functions. "
            f"Written to {test_file_path}"
        )

    except Exception as e:
        logger.error(f"[Test Generator] Failed: {e}")
        state["workflow_status"]["test_generator"] = "failed"
        state["errors"] = state.get("errors", []) + [f"Test Generator: {str(e)}"]
        # Provide minimal fallback test
        state["test_cases"] = _minimal_fallback_tests()
        project_path = Path(state.get("project_path", "."))
        (project_path / "test_ai_generated.py").write_text(state["test_cases"])
        state["test_file_path"] = str(project_path / "test_ai_generated.py")

    return state


def _extract_python_code(raw: str) -> str:
    """Extract Python code from a markdown-fenced response."""
    # Remove ```python ... ``` fences
    match = re.search(r"```python\s*(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Remove plain ``` fences
    match = re.search(r"```\s*(.*?)```", raw, re.DOTALL)
    if match:
        return match.group(1).strip()

    # Return as-is if no fences found
    return raw.strip()


def _count_test_functions(code: str) -> int:
    """Count the number of test functions in generated code."""
    return sum(1 for line in code.splitlines() if line.strip().startswith("def test_"))


def _minimal_fallback_tests() -> str:
    """Emergency fallback: minimal tests that will always run."""
    return '''"""
AI-Generated test cases (fallback mode).
"""
import pytest


def test_basic_python():
    """Verify Python is working."""
    assert 1 + 1 == 2


def test_string_operations():
    """Basic string test."""
    s = "Hello, World!"
    assert len(s) > 0
    assert s.lower() == "hello, world!"


def test_list_operations():
    """Basic list operations."""
    lst = [1, 2, 3, 4, 5]
    assert len(lst) == 5
    assert sum(lst) == 15
    assert max(lst) == 5
'''
