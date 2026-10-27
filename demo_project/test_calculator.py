"""
Existing baseline tests for calculator - intentionally missing edge cases.
"""

from calculator import add, divide, multiply, subtract


def test_add_positive():
    assert add(2, 3) == 5


def test_add_negative():
    assert add(-1, -1) == -2


def test_subtract():
    assert subtract(10, 5) == 5


def test_multiply():
    assert multiply(3, 4) == 12


def test_divide_normal():
    assert divide(10, 2) == 5.0

# Intentionally missing:
# - test_divide_by_zero (edge case)
# - test_calculate_discount_invalid
# - test_factorial_negative
# - test_average_empty
