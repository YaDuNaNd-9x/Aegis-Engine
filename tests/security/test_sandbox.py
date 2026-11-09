
import pytest

from backend.app.sandbox.policies import (
    validate_code,
    CodePolicyError,
)


@pytest.mark.parametrize(
    "code",
    [
        "import os",
        "import sys",
        "import subprocess",
        "open('/tmp/test.txt', 'w')",
        "eval('2 + 2')",
        "exec('print(1)')",
        "df.__class__",
        "globals()",
        "locals()",
    ],
)
def test_sandbox_blocks_dangerous_operations(code):

    with pytest.raises(CodePolicyError):
        validate_code(code)


def test_sandbox_accepts_safe_dataframe_operations():

    code = """
result = {
    "row_count": int(len(df)),
    "average": float(df["temperature_c"].mean())
}
"""

    assert validate_code(code) is True


def test_sandbox_rejects_infinite_loop():

    code = """
while True:
    pass
"""

    with pytest.raises(CodePolicyError):
        validate_code(code)


def test_sandbox_rejects_file_access():

    code = """
result = open("/etc/passwd").read()
"""

    with pytest.raises(CodePolicyError):
        validate_code(code)


def test_sandbox_rejects_dynamic_execution():

    code = """
result = eval("1 + 1")
"""

    with pytest.raises(CodePolicyError):
        validate_code(code)
