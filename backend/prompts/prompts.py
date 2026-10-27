"""
All LLM prompts for the AI QA Engineer system.
Centralizing prompts makes them easy to tune and version.
"""


def code_analysis_prompt(filename: str, source_code: str) -> str:
    return f"""You are an expert Python code reviewer and software quality engineer.

Analyze the following Python file for code quality issues.

File: {filename}

Source Code:
```python
{source_code}
```

Provide a detailed analysis including:
1. Code complexity assessment
2. Naming convention issues
3. Missing error handling
4. Code smells
5. Documentation gaps
6. Maintainability concerns

Be specific about line numbers where issues occur.
Focus on actionable findings that a developer can fix.
"""


def test_generation_prompt(source_files: dict) -> str:
    file_contents = "\n\n".join(
        f"=== {fname} ===\n```python\n{code}\n```"
        for fname, code in source_files.items()
    )
    return f"""You are an expert Python test engineer. 
Generate comprehensive pytest unit tests for the following Python source code.

{file_contents}

Requirements:
1. Generate pytest test classes and functions
2. Test normal cases, edge cases, and error cases
3. Include tests that will FAIL to demonstrate bugs (document why they fail)
4. Use pytest.raises() for expected exceptions
5. Add clear docstrings explaining what each test verifies
6. Make tests that will realistically run against the actual code

IMPORTANT: Return ONLY valid Python code with no markdown fences.
Start directly with import statements.
"""


def bug_analysis_prompt(
    source_files: dict,
    test_results: dict,
    code_quality: dict,
    security: dict,
) -> str:
    failed_tests = test_results.get("failed", [])
    ruff_issues = code_quality.get("issues", [])
    security_issues = security.get("findings", [])

    return f"""You are an expert software QA engineer and bug analyst.

Analyze the following information and identify bugs in the codebase.

FAILED TESTS:
{failed_tests}

CODE QUALITY ISSUES:
{ruff_issues[:10]}

SECURITY FINDINGS:
{security_issues[:10]}

SOURCE FILES:
{list(source_files.keys())}

Identify all bugs and return a JSON array with this exact structure:
[
  {{
    "bug_id": "BUG-001",
    "severity": "Critical|Major|Minor",
    "category": "Runtime Error|Logic Error|Security|Performance|Code Quality",
    "file": "filename.py",
    "line": 42,
    "function": "function_name",
    "description": "Clear description of the bug",
    "confidence": 95
  }}
]

Return ONLY the JSON array, no other text.
"""


def root_cause_prompt(bug: dict, source_code: str) -> str:
    return f"""You are an expert software engineer performing root cause analysis.

Bug Report:
- Bug ID: {bug.get('bug_id')}
- Severity: {bug.get('severity')}
- File: {bug.get('file')}
- Line: {bug.get('line')}
- Function: {bug.get('function')}
- Description: {bug.get('description')}

Relevant Source Code:
```python
{source_code[:2000]}
```

Perform a root cause analysis and return a JSON object with this structure:
{{
  "root_cause": "Specific technical explanation of WHY this bug exists",
  "affected_component": "file.py → function_name()",
  "fix_suggestion": "Exact code change or approach to fix this",
  "fix_complexity": "Low|Medium|High",
  "confidence": 95,
  "business_impact": "Impact on the business/users if not fixed",
  "technical_impact": "Technical consequences of this bug"
}}

Return ONLY the JSON object, no other text.
"""


def qa_report_prompt(
    project_info: dict,
    quality_score: int,
    security_score: int,
    test_pass_rate: float,
    coverage: float,
    bug_count: int,
    critical_count: int,
    major_count: int,
    minor_count: int,
) -> str:
    return f"""You are a senior QA manager writing an executive summary for a software quality report.

Project: {project_info.get('name', 'Demo Project')}
Files Analyzed: {project_info.get('file_count', 0)}
Total Lines: {project_info.get('total_lines', 0)}

Quality Metrics:
- Overall Quality Score: {quality_score}/100
- Security Score: {security_score}/100
- Test Pass Rate: {test_pass_rate:.1f}%
- Code Coverage: {coverage:.1f}%
- Total Bugs: {bug_count}
- Critical Issues: {critical_count}
- Major Issues: {major_count}
- Minor Issues: {minor_count}

Write a professional 3-paragraph executive summary:
1. Overall assessment of the codebase quality
2. Key risks and their business impact
3. Recommendations and priority actions

Be concise, professional, and actionable.
"""
