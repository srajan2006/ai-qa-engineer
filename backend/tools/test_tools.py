"""
Test execution helper functions.
"""

import re
from typing import Any


def parse_pytest_summary(output: str) -> dict[str, Any]:
    """Parse pytest summary lines from stdout/stderr."""
    res = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
    for line in output.splitlines():
        if "passed" in line or "failed" in line or "error" in line:
            for key in ["passed", "failed", "error", "skipped"]:
                match = re.search(rf"(\d+)\s+{key}", line)
                if match:
                    val = int(match.group(1))
                    if key == "error":
                        res["errors"] += val
                    else:
                        res[key] += val
    return res
