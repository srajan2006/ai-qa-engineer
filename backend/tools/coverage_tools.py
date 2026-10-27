"""
Coverage measurement tool helpers.
"""

from typing import Any


def format_coverage_table(file_coverage: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    """Format coverage dictionary into tabular structure."""
    table = []
    for filename, stats in file_coverage.items():
        table.append({
            "filename": filename,
            "covered": stats.get("covered", 0),
            "total": stats.get("total", 0),
            "percentage": stats.get("percentage", 0.0),
        })
    return table
