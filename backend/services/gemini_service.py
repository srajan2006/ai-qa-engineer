"""
Centralized Gemini service with automatic fallback to demo mode.

Uses the google-genai SDK (NOT the deprecated google-generativeai).
"""

import json
import random
from typing import Optional

from loguru import logger

from backend.config import DEMO_MODE, GEMINI_API_KEY, GEMINI_MODEL


class GeminiService:
    """Gemini LLM service with graceful fallback to mock responses."""

    def __init__(self):
        self._client = None
        self._available = False
        self._init_client()

    def _init_client(self):
        """Initialize the Gemini client if API key is available."""
        if DEMO_MODE or not GEMINI_API_KEY:
            logger.info("GeminiService: Running in DEMO/MOCK mode (no API key).")
            self._available = False
            return

        try:
            from google import genai  # type: ignore

            self._client = genai.Client(api_key=GEMINI_API_KEY)
            self._available = True
            logger.info(f"GeminiService: Connected to Gemini ({GEMINI_MODEL})")
        except Exception as e:
            logger.warning(f"GeminiService: Failed to initialize Gemini client: {e}")
            self._available = False

    @property
    def is_demo_mode(self) -> bool:
        return not self._available

    def generate(self, prompt: str, max_retries: int = 2) -> str:
        """
        Send a prompt to Gemini and return the text response.
        Falls back to a structured mock response if unavailable.
        """
        if not self._available:
            return self._mock_response(prompt)

        for attempt in range(max_retries + 1):
            try:
                response = self._client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=prompt,
                )
                return response.text or ""
            except Exception as e:
                logger.warning(f"Gemini API attempt {attempt + 1} failed: {e}")
                if attempt == max_retries:
                    logger.error("Gemini API unavailable — switching to mock mode.")
                    self._available = False
                    return self._mock_response(prompt)

        return self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """
        Generate a realistic-looking AI response for demo mode.
        Returns context-aware mock data based on keywords in the prompt.
        """
        prompt_lower = prompt.lower()

        if "generate" in prompt_lower and "test" in prompt_lower:
            return self._mock_test_generation()
        elif "root cause" in prompt_lower or "rca" in prompt_lower:
            return self._mock_root_cause()
        elif "bug" in prompt_lower and ("analyz" in prompt_lower or "identif" in prompt_lower):
            return self._mock_bug_analysis()
        elif "security" in prompt_lower:
            return self._mock_security_analysis()
        elif "report" in prompt_lower or "summary" in prompt_lower:
            return self._mock_report_narrative()
        else:
            return self._mock_generic_analysis()

    def _mock_test_generation(self) -> str:
        return '''```python
import pytest
from calculator import add, subtract, multiply, divide, calculate_discount, average, factorial


class TestAdd:
    def test_add_positive_numbers(self):
        assert add(2, 3) == 5

    def test_add_negative_numbers(self):
        assert add(-2, -3) == -5

    def test_add_zero(self):
        assert add(0, 5) == 5

    def test_add_floats(self):
        assert abs(add(1.1, 2.2) - 3.3) < 1e-9


class TestDivide:
    def test_divide_normal(self):
        assert divide(10, 2) == 5.0

    def test_divide_by_zero(self):
        """This test WILL FAIL - demonstrates the bug."""
        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

    def test_divide_negative(self):
        assert divide(-10, 2) == -5.0


class TestCalculateDiscount:
    def test_valid_discount(self):
        assert calculate_discount(100, 10) == 90.0

    def test_negative_discount_raises(self):
        with pytest.raises(ValueError):
            calculate_discount(100, -5)

    def test_discount_over_100(self):
        """This will NOT raise but will give negative price - bug!"""
        result = calculate_discount(100, 150)
        assert result >= 0, "Discounted price should not be negative"


class TestAverage:
    def test_average_normal(self):
        assert average([1, 2, 3, 4, 5]) == 3.0

    def test_average_empty_list(self):
        """This test WILL FAIL - demonstrates the empty list bug."""
        with pytest.raises(ZeroDivisionError):
            average([])

    def test_average_single_element(self):
        assert average([42]) == 42.0


class TestFactorial:
    def test_factorial_zero(self):
        assert factorial(0) == 1

    def test_factorial_positive(self):
        assert factorial(5) == 120

    def test_factorial_negative(self):
        """This test WILL FAIL - demonstrates negative input bug."""
        with pytest.raises((ValueError, RecursionError)):
            factorial(-1)
```'''

    def _mock_root_cause(self) -> str:
        return json.dumps({
            "root_cause": "The function performs division without validating the denominator. "
                          "When the denominator is zero, Python raises a ZeroDivisionError which is "
                          "not caught, causing the application to crash.",
            "affected_component": "calculator.py → divide()",
            "fix_suggestion": "Add a guard clause before division: if b == 0: raise ValueError('Denominator cannot be zero')",
            "fix_complexity": "Low",
            "confidence": 96,
            "business_impact": "Any calculation involving division by zero will crash the application, "
                               "potentially causing data loss or service disruption.",
            "technical_impact": "Unhandled ZeroDivisionError propagates up the call stack."
        })

    def _mock_bug_analysis(self) -> str:
        return json.dumps([
            {
                "bug_id": "BUG-001",
                "severity": "Critical",
                "category": "Runtime Error",
                "file": "calculator.py",
                "line": 22,
                "function": "divide",
                "description": "Division by zero: function does not validate denominator before dividing.",
                "confidence": 98
            },
            {
                "bug_id": "BUG-002",
                "severity": "Critical",
                "category": "Security",
                "file": "user_service.py",
                "line": 11,
                "function": "module-level",
                "description": "Hardcoded API key and secret found in source code.",
                "confidence": 99
            },
            {
                "bug_id": "BUG-003",
                "severity": "Critical",
                "category": "Security",
                "file": "database.py",
                "line": 38,
                "function": "get_user",
                "description": "SQL injection vulnerability: user input directly interpolated into SQL query.",
                "confidence": 97
            },
            {
                "bug_id": "BUG-004",
                "severity": "Major",
                "category": "Runtime Error",
                "file": "calculator.py",
                "line": 55,
                "function": "average",
                "description": "ZeroDivisionError on empty list: no length check before dividing by len(numbers).",
                "confidence": 95
            },
            {
                "bug_id": "BUG-005",
                "severity": "Major",
                "category": "Logic Error",
                "file": "calculator.py",
                "line": 40,
                "function": "calculate_discount",
                "description": "Discount over 100% produces negative price. No upper bound validation.",
                "confidence": 92
            },
            {
                "bug_id": "BUG-006",
                "severity": "Minor",
                "category": "Code Quality",
                "file": "utils.py",
                "line": 20,
                "function": "fn1",
                "description": "Poor function name 'fn1' provides no context about the function's purpose.",
                "confidence": 88
            }
        ])

    def _mock_security_analysis(self) -> str:
        return "Security analysis complete with critical findings identified."

    def _mock_report_narrative(self) -> str:
        return (
            "The AI QA Engineer has completed a comprehensive analysis of the demo project. "
            "The codebase demonstrates several common but serious quality and security issues "
            "that are frequently found in real-world projects. Critical security vulnerabilities "
            "including SQL injection and hardcoded credentials require immediate remediation. "
            "The division-by-zero bug in the calculator module indicates insufficient input "
            "validation practices. The overall code quality score reflects these findings, "
            "and the development team is advised to prioritize security fixes before deployment. "
            "Test coverage is below the recommended 80% threshold and should be improved."
        )

    def _mock_generic_analysis(self) -> str:
        return (
            "Analysis complete. The code shows several areas for improvement including "
            "input validation, error handling, and security practices. "
            "Recommend addressing critical issues before production deployment."
        )


# Singleton instance
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get or create the singleton Gemini service."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
