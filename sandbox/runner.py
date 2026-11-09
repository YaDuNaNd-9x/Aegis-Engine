import contextlib
import io
import json
import sys
import traceback

import numpy as np
import pandas as pd


MAX_OUTPUT_CHARS = 20000
MAX_ROWS = 100000
MAX_COLUMNS = 200
MAX_CODE_CHARS = 20000


def emit(payload: dict, exit_code: int = 0):
    """Write one machine-readable JSON response."""

    print(
        json.dumps(payload, default=str),
        flush=True,
    )

    sys.exit(exit_code)


def main():
    try:
        code = sys.stdin.read(MAX_CODE_CHARS + 1)

        if not code.strip():
            raise ValueError("No analysis code received.")

        if len(code) > MAX_CODE_CHARS:
            raise ValueError("Analysis code exceeds the size limit.")

        df = pd.read_csv(
            "/input/dataset.csv",
            low_memory=False,
        )

        if df.empty:
            raise ValueError("Uploaded dataset contains no rows.")

        if len(df) > MAX_ROWS:
            raise ValueError(
                f"Dataset exceeds the {MAX_ROWS}-row sandbox limit."
            )

        if len(df.columns) > MAX_COLUMNS:
            raise ValueError(
                f"Dataset exceeds the {MAX_COLUMNS}-column sandbox limit."
            )

        safe_builtins = {
            "float": float,
            "int": int,
            "str": str,
            "len": len,
            "round": round,
            "min": min,
            "max": max,
            "abs": abs,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "sum": sum,
            "print": print,
            "enumerate": enumerate,
            "sorted": sorted,
            "zip": zip,
        }

        namespace = {
            "__builtins__": safe_builtins,
            "pd": pd,
            "np": np,
            "df": df,
            "result": None,
        }

        captured_output = io.StringIO()

        with contextlib.redirect_stdout(captured_output):
            exec(
                compile(code, "<analysis>", "exec"),
                namespace,
                namespace,
            )

        result = namespace.get("result")

        if not isinstance(result, dict):
            raise ValueError(
                "Analysis code must assign a dictionary to 'result'."
            )

        # Confirm that the result can be serialized before returning it.
        serialized_result = json.dumps(
            result,
            default=str,
        )

        if len(serialized_result) > MAX_OUTPUT_CHARS:
            raise ValueError(
                "Analysis result exceeds the permitted output size."
            )

        output = {
            "status": "success",
            "result": json.loads(serialized_result),
            "printed_output": captured_output.getvalue()[
                :MAX_OUTPUT_CHARS
            ],
            "rows_processed": len(df),
            "columns": [str(column) for column in df.columns],
        }

        emit(output)

    except Exception as exc:
        emit(
            {
                "status": "error",
                "error": str(exc),
                "traceback": traceback.format_exc()[-3000:],
            },
            exit_code=1,
        )


if __name__ == "__main__":
    main()