"""
Security scanning patterns and tool helpers.
"""

from typing import Any

SECURITY_RULES = [
    {
        "pattern": "subprocess.run",
        "code": "B603",
        "severity": "High",
        "description": "Subprocess execution detected. Ensure command arguments are sanitized.",
    },
    {
        "pattern": "shell=True",
        "code": "B602",
        "severity": "Critical",
        "description": "subprocess.run with shell=True is vulnerable to command injection.",
    },
    {
        "pattern": "eval(",
        "code": "B307",
        "severity": "Critical",
        "description": "Direct eval() execution allows arbitrary code injection.",
    },
    {
        "pattern": "pickle.load",
        "code": "B301",
        "severity": "Critical",
        "description": "Insecure deserialization via pickle allows remote code execution.",
    },
    {
        "pattern": "SECRET_KEY",
        "code": "B105",
        "severity": "Critical",
        "description": "Hardcoded secret key detected in source code.",
    },
    {
        "pattern": "API_KEY",
        "code": "B105",
        "severity": "Critical",
        "description": "Hardcoded API key detected in source code.",
    },
    {
        "pattern": "hashlib.md5",
        "code": "B324",
        "severity": "High",
        "description": "MD5 hash algorithm is cryptographically insecure.",
    },
]


def run_heuristic_security_scan(source_files: dict[str, str]) -> list[dict[str, Any]]:
    """Scan files using predefined security heuristics."""
    findings = []
    for fname, code in source_files.items():
        lines = code.splitlines()
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for rule in SECURITY_RULES:
                if rule["pattern"] in stripped:
                    findings.append({
                        "file": fname,
                        "line": idx,
                        "code": rule["code"],
                        "severity": rule["severity"],
                        "description": rule["description"],
                        "confidence": "High",
                    })
    return findings
