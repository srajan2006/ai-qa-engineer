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