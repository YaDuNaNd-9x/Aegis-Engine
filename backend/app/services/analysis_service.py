import io
import re

import pandas as pd

from backend.app.llm.ollama_client import ollama_client
from backend.app.sandbox.executor import sandbox_executor
from backend.app.core.config import settings


class AnalysisService:

    async def generate_analysis_code(
        self,
        instruction: str,
        columns: list[str],
    ) -> str:
        """
        Generate restricted pandas/numpy analysis code.
        """

        system_prompt = """
You are the AEGIS ENGINE industrial data analysis code generator.

Generate Python code using ONLY:
- pandas as pd
- numpy as np
- the provided dataframe df

Available variables:
- df: uploaded CSV as a pandas DataFrame
- pd: pandas
- np: numpy

STRICT REQUIREMENTS:

1. Never use imports.
2. Never use file access, network access or system commands.
3. Never use open, eval, exec, subprocess or input.
4. Do not modify the original dataframe.
5. Do not use loops, functions, classes or exception handling.
6. Assign the final output to a variable named result.
7. result MUST be a dictionary.
8. Values must be JSON-compatible.
9. Use only the columns supplied by the user.
10. Do not invent measurements or readings.
11. Do not use markdown fences.
12. Keep calculations concise.

Expected output structure:

result = {
    "summary": "Analysis summary",
    "statistics": {},
    "findings": [],
    "recommendations": []
}

Return ONLY Python source code.
"""

        user_prompt = (
            f"Analysis request:\n{instruction}\n\n"
            f"Available CSV columns:\n{columns}\n\n"
            "Generate the Python analysis code."
        )

        model_name = getattr(
            settings,
            "REASONING_MODEL",
            "qwen2.5:7b",
        )

        response = await ollama_client.chat(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            model=model_name,
            temperature=0,
        )

        if isinstance(response, dict):
            code = (
                response.get("message", {}).get("content")
                or response.get("response")
                or ""
            )
        else:
            code = str(response)

        code = code.strip()

        code = re.sub(
            r"^```(?:python)?\s*",
            "",
            code,
            flags=re.IGNORECASE,
        )

        code = re.sub(
            r"\s*```$",
            "",
            code,
        )

        code = code.strip()

        if not code:
            raise ValueError(
                "The local model did not generate analysis code."
            )

        return code

    async def analyze(
        self,
        instruction: str,
        csv_bytes: bytes,
    ) -> dict:
        """
        Generate, validate and execute CSV analysis.
        """

        if not instruction or not instruction.strip():
            raise ValueError("Analysis instruction cannot be empty.")

        if len(instruction) > 3000:
            raise ValueError("Analysis instruction is too long.")

        if not csv_bytes:
            raise ValueError("Uploaded dataset is empty.")

        if len(csv_bytes) > 25 * 1024 * 1024:
            raise ValueError("Dataset exceeds the 25 MB limit.")

        try:
            dataframe = pd.read_csv(
                io.BytesIO(csv_bytes),
                nrows=1000,
            )

        except Exception as exc:
            raise ValueError(
                f"Unable to read uploaded CSV: {exc}"
            ) from exc

        if dataframe.empty:
            raise ValueError("Uploaded dataset is empty.")

        if len(dataframe.columns) == 0:
            raise ValueError("CSV contains no usable columns.")

        columns = [
            str(column)
            for column in dataframe.columns
        ]

        steps = [
            "Dataset received.",
            f"Detected {len(columns)} columns.",
            f"Previewed {len(dataframe)} rows.",
            "Generating analysis code using the local reasoning model.",
        ]

        code = await self.generate_analysis_code(
            instruction,
            columns,
        )

        steps.append("Analysis code generated.")

        execution = await sandbox_executor.execute(
            code,
            csv_bytes,
        )

        if execution.get("status") == "success":
            steps.append(
                "Sandbox execution completed successfully."
            )
        else:
            steps.append(
                "Sandbox execution did not succeed."
            )

        return {
            "status": execution.get("status", "error"),
            "result": execution.get("result"),
            "error": execution.get("error"),
            "explanation": execution.get("printed_output"),
            "execution_steps": steps,
        }


analysis_service = AnalysisService()