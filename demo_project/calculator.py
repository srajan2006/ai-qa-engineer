"""
Calculator module - intentionally contains several realistic bugs for demo purposes.
"""


def add(a, b):
    """Add two numbers."""
    return a + b


def subtract(a, b):
    """Subtract b from a."""
    return a - b


def multiply(a, b):
    """Multiply two numbers."""
    return a * b


def divide(a, b):
    """Divide a by b.
    BUG: No zero-division check! Raises ZeroDivisionError without guard.
    """
    return a / b


def calculate_discount(price, discount_percent):
    """Calculate discounted price.
    BUG: Wrong conditional logic - negative discount raises, but discount > 100
    gives negative price (no upper-bound validation).
    """
    if discount_percent < 0:
        raise ValueError("Discount cannot be negative")
    # BUG: No upper bound check (e.g. discount > 100 leads to negative price)
    discounted = price - (price * discount_percent / 100)
    return discounted


def factorial(n):
    """Calculate factorial.
    BUG: No handling for negative numbers (causes infinite recursion / RecursionError).
    """
    if n == 0:
        return 1
    return n * factorial(n - 1)


def average(numbers):
    """Calculate average of a list.
    BUG: No empty list check (ZeroDivisionError on len(numbers)==0).
    """
    total = 0
    for num in numbers:
        total = total + num
    return total / len(numbers)


# Code Smell: Unused constants
PI = 3.14159
UNUSED_CONSTANT = 42


def area_of_circle(radius):
    """Calculate area of circle using hardcoded PI instead of math.pi."""
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return PI * radius * radius
