import asyncio
import json
import tempfile
import uuid

from pathlib import Path

from backend.app.sandbox.policies import (
    validate_code,
    CodePolicyError,
)


SANDBOX_IMAGE = "aegis-analysis-sandbox:1.0"

EXECUTION_TIMEOUT = 15
MAX_MEMORY = "256m"
MAX_CPUS = "1.0"
MAX_PIDS = 64

MAX_CSV_SIZE = 25 * 1024 * 1024
MAX_OUTPUT_SIZE = 1024 * 1024


class SandboxExecutor:
    """
    Execute validated analysis code in an isolated Docker container.

    Container controls:
    - Network disabled
    - Non-root user
    - Read-only root filesystem
    - Read-only dataset mount
    - Memory and CPU limits
    - PID limit
    - Linux capabilities dropped
    - No-new-privileges
    - Restricted temporary filesystem
    - Execution timeout
    - Automatic container cleanup
    """

    async def _kill_container(
        self,
        container_name: str,
    ) -> None:
        try:
            process = await asyncio.create_subprocess_exec(
                "docker",
                "kill",
                container_name,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )

            await asyncio.wait_for(
                process.communicate(),
                timeout=3,
            )

        except Exception:
            pass

    async def execute(
        self,
        code: str,
        csv_bytes: bytes,
    ) -> dict:

        try:
            validate_code(code)

        except CodePolicyError as exc:
            return {
                "status": "blocked",
                "error": str(exc),
            }

        if not csv_bytes:
            return {
                "status": "error",
                "error": "Dataset is empty.",
            }

        if len(csv_bytes) > MAX_CSV_SIZE:
            return {
                "status": "error",
                "error": "Dataset exceeds the 25 MB sandbox limit.",
            }

        container_name = f"aegis-analysis-{uuid.uuid4().hex[:12]}"

        with tempfile.TemporaryDirectory(
            prefix="aegis_sandbox_"
        ) as temp_dir:

            dataset_path = Path(temp_dir) / "dataset.csv"

            try:
                dataset_path.write_bytes(csv_bytes)
                dataset_path.chmod(0o644)

                command = [
                    "docker",
                    "run",
                    "--rm",
                    "--name", container_name,
                    "-i",
                    "--network=none",
                    "--read-only",
                    "--user=10001:10001",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges",
                    "--pids-limit", str(MAX_PIDS),
                    f"--memory={MAX_MEMORY}",
                    "--memory-swap", MAX_MEMORY,
                    f"--cpus={MAX_CPUS}",
                    "--tmpfs=/tmp:rw,noexec,nosuid,nodev,size=16m",
                    "--mount",
                    (
                        f"type=bind,source={dataset_path.resolve()},"
                        "target=/input/dataset.csv,readonly"
                    ),
                    SANDBOX_IMAGE,
                ]

                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )

                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(code.encode("utf-8")),
                        timeout=EXECUTION_TIMEOUT,
                    )

                except asyncio.TimeoutError:
                    await self._kill_container(container_name)

                    if process.returncode is None:
                        process.kill()
                        await process.communicate()

                    return {
                        "status": "timeout",
                        "error": (
                            f"Analysis exceeded the "
                            f"{EXECUTION_TIMEOUT}-second execution limit."
                        ),
                    }

                if len(stdout) > MAX_OUTPUT_SIZE:
                    return {
                        "status": "error",
                        "error": "Sandbox output exceeded the permitted size.",
                    }

                try:
                    output = json.loads(
                        stdout.decode("utf-8")
                    )

                except (json.JSONDecodeError, UnicodeDecodeError):
                    error_message = stderr.decode(
                        "utf-8",
                        errors="replace",
                    )[-4000:]

                    return {
                        "status": "error",
                        "error": (
                            error_message
                            or "Sandbox returned invalid JSON output."
                        ),
                    }

                if not isinstance(output, dict):
                    return {
                        "status": "error",
                        "error": "Sandbox returned an invalid response.",
                    }

                if process.returncode != 0 and output.get("status") == "success":
                    return {
                        "status": "error",
                        "error": "Sandbox process exited unexpectedly.",
                    }

                return output

            except FileNotFoundError:
                return {
                    "status": "error",
                    "error": "Docker executable was not found.",
                }

            except Exception as exc:
                await self._kill_container(container_name)

                return {
                    "status": "error",
                    "error": f"Sandbox execution failed: {exc}",
                }


sandbox_executor = SandboxExecutor()