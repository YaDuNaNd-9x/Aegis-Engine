
import pytest

from backend.app.sandbox.policies import (
    validate_code,
    CodePolicyError,
)


def test_valid_dataframe_analysis():
    code = """
result = {
    "average": float(df["temperature_c"].mean()),
    "maximum": float(df["temperature_c"].max()),
}
"""
    assert validate_code(code) is True


def test_valid_numpy_analysis():
    code = """
result = {
    "mean": float(np.mean(df["temperature_c"])),
    "count": int(len(df)),
}
"""
    assert validate_code(code) is True


@pytest.mark.parametrize(
    "code",
    [
        "import os",
        "import subprocess",
        "import sys",
        "from pathlib import Path",
        "open('/etc/passwd')",
        "eval('1 + 1')",
        "exec('print(1)')",
        "globals()",
        "locals()",
        "getattr(df, '__class__')",
        "df.__class__",
    ],
)
def test_dangerous_code_is_rejected(code):
    with pytest.raises(CodePolicyError):
        validate_code(code)


@pytest.mark.parametrize(
    "code",
    [
        "while True:\n    pass",
        "for i in range(10):\n    pass",
        "lambda x: x",
        "class Example:\n    pass",
        "try:\n    pass\nexcept:\n    pass",
        "def example():\n    global x",
    ],
)
def test_restricted_python_constructs_are_rejected(code):
    with pytest.raises(CodePolicyError):
        validate_code(code)


def test_empty_code_is_rejected():
    with pytest.raises((CodePolicyError, ValueError)):
        validate_code("")


def test_invalid_python_syntax_is_rejected():
    with pytest.raises((CodePolicyError, SyntaxError)):
        validate_code("result = {")
