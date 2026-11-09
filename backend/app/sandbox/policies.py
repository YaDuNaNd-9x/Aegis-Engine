import ast


MAX_CODE_LENGTH = 20000

BLOCKED_NAMES = {
    "open", "exec", "eval", "compile", "input",
    "globals", "locals", "vars", "getattr", "setattr",
    "delattr", "__import__", "breakpoint",
    "help", "memoryview", "exit", "quit",
}

BLOCKED_ATTRIBUTES = {
    "__class__", "__dict__", "__globals__",
    "__builtins__", "__subclasses__", "__mro__",
    "__bases__", "__code__", "__getattribute__",
    "__reduce__", "__reduce_ex__", "__closure__",
}

BLOCKED_NODES = (
    ast.Import,
    ast.ImportFrom,
    ast.Global,
    ast.Nonlocal,
    ast.Lambda,
    ast.ClassDef,
    ast.FunctionDef,
    ast.AsyncFunctionDef,
    ast.Await,
    ast.Yield,
    ast.YieldFrom,
    ast.With,
    ast.AsyncWith,
    ast.Try,
    ast.Raise,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.Delete,
)


class CodePolicyError(Exception):
    """Raised when generated analysis code violates sandbox policy."""


def validate_code(code: str) -> bool:
    """
    Validate AI-generated Python before Docker execution.

    This is a defense-in-depth check, not a replacement
    for operating-system/container isolation.
    """

    if not isinstance(code, str) or not code.strip():
        raise CodePolicyError("Analysis code is empty.")

    if len(code) > MAX_CODE_LENGTH:
        raise CodePolicyError("Analysis code exceeds the permitted size.")

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise CodePolicyError(
            f"Invalid Python syntax: {exc}"
        ) from exc

    for node in ast.walk(tree):

        if isinstance(node, BLOCKED_NODES):
            raise CodePolicyError(
                f"Disallowed Python construct: {type(node).__name__}"
            )

        if isinstance(node, ast.Name):
            if (
                node.id in BLOCKED_NAMES
                or node.id.startswith("__")
            ):
                raise CodePolicyError(
                    f"Disallowed name: {node.id}"
                )

        if isinstance(node, ast.Attribute):
            if (
                node.attr in BLOCKED_ATTRIBUTES
                or node.attr.startswith("__")
            ):
                raise CodePolicyError(
                    f"Disallowed attribute: {node.attr}"
                )

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id in BLOCKED_NAMES:
                    raise CodePolicyError(
                        f"Blocked function: {node.func.id}"
                    )

        # Prevent generated code from replacing the execution environment.
        if isinstance(node, ast.Name) and node.id == "__builtins__":
            raise CodePolicyError(
                "Access to Python builtins is prohibited."
            )

    if not any(
        isinstance(node, ast.Name) and node.id == "result"
        for node in ast.walk(tree)
    ):
        raise CodePolicyError(
            "Analysis code must assign its output to 'result'."
        )

    return True