"""
Utility functions - contains insecure deserialization, eval execution, and poor code style.
"""

import os
import pickle


def fn1(x, y, z):
    """BUG: Poor naming convention and obscure signature."""
    return x + y - z


def load_config(filepath):
    """Load configuration from file.
    CRITICAL SECURITY VULNERABILITY: Insecure deserialization via pickle!
    """
    with open(filepath, "rb") as f:
        return pickle.load(f)


def read_file(filename):
    """Read a local file without path traversal protection or error handling."""
    with open(filename, "r", encoding="utf-8") as f:
        return f.read()


def parse_user_input(user_input):
    """Parse user input expression.
    CRITICAL VULNERABILITY: eval() on unsanitized user input allows arbitrary code execution.
    """
    result = eval(user_input)
    return result


def format_output(data, unused_param=None):
    """Format output data.
    CODE SMELL: unused parameter.
    """
    return str(data)


def check_age(age):
    """Validate age.
    BUG: Upper bound not checked (e.g. age=999 returns True).
    """
    if age < 0:
        return False
    return True


def get_env_variable(key):
    """Get environment variable."""
    return os.environ.get(key)
