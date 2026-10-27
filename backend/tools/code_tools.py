"""
Code quality and static analysis helper tools.
"""

import ast
from pathlib import Path
from typing import Any


def analyze_ast_tree(tree: ast.AST) -> dict[str, Any]:
    """Extract AST level metrics like functions, classes, complexity and docstrings."""
    functions = 0
    classes = 0
    complexity = 1
    docstrings_missing = 0

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions += 1
            for child in ast.walk(node):
                if isinstance(
                    child,
                    (
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.ExceptHandler,
                        ast.With,
                        ast.Assert,
                        ast.BoolOp,
                    ),
                ):
                    complexity += 1
            if not (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
            ):
                docstrings_missing += 1
        elif isinstance(node, ast.ClassDef):
            classes += 1

    return {
        "functions": functions,
        "classes": classes,
        "complexity": complexity,
        "docstrings_missing": docstrings_missing,
    }


def read_python_files(directory: Path) -> dict[str, str]:
    """Scan and read all python files in directory."""
    files: dict[str, str] = {}
    for p in directory.rglob("*.py"):
        if any(part in ("__pycache__", ".venv", "venv", ".git") for part in p.parts):
            continue
        try:
            rel = str(p.relative_to(directory))
            files[rel] = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            pass
    return files
