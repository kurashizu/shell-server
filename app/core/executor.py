from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

from .jail import SecurityError, validate_command


class Executor:
    """Runs commands in a sandboxed environment with timeout & output limits."""

    def __init__(
        self,
        allowed_commands: list[str],
        max_output_size: int,
        default_timeout: int,
        max_timeout: int,
    ) -> None:
        self.allowed_commands = allowed_commands
        self.max_output_size = max_output_size
        self.default_timeout = default_timeout
        self.max_timeout = max_timeout

    # ------------------------------------------------------------------
    # Blocking exec (waits for full output, returns at once)
    # ------------------------------------------------------------------

    async def execute(
        self,
        command: str,
        args: list[str],
        timeout_secs: int | None,
        env: dict[str, str] | None,
        cwd: Path,
        shell: bool = False,
    ) -> dict:
        """Run a command and return its result as a dict."""
        timeout = min(timeout_secs or self.default_timeout, self.max_timeout)

        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        start = time.monotonic()

        if shell:
            shell_cmd = " ".join([command] + args)
            validate_command(_first_token(shell_cmd), [], self.allowed_commands)
            try:
                process = await asyncio.create_subprocess_exec(
                    "bash",
                    "-c",
                    shell_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                    env=cmd_env,
                )
            except FileNotFoundError:
                return _result(
                    exit_code=-1, error="bash not found (shell mode requires bash)"
                )
        else:
            validate_command(command, args, self.allowed_commands)
            try:
                process = await asyncio.create_subprocess_exec(
                    command,
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                    env=cmd_env,
                )
            except FileNotFoundError:
                return _result(exit_code=-1, error=f"Command not found: {command}")

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            return _result(
                exit_code=-1,
                duration_ms=(time.monotonic() - start) * 1000,
                error=f"Timed out after {timeout}s",
            )

        duration = (time.monotonic() - start) * 1000
        stdout_str = stdout.decode("utf-8", errors="replace")
        stderr_str = stderr.decode("utf-8", errors="replace")
        truncated = False

        if len(stdout_str) > self.max_output_size:
            stdout_str = stdout_str[: self.max_output_size] + "\n... [truncated]"
            truncated = True
        if len(stderr_str) > self.max_output_size:
            stderr_str = stderr_str[: self.max_output_size] + "\n... [truncated]"
            truncated = True

        return _result(
            stdout=stdout_str,
            stderr=stderr_str,
            exit_code=process.returncode,
            duration_ms=duration,
            truncated=truncated,
        )

    # ------------------------------------------------------------------
    # Streaming exec (SSE – yields dict events as output arrives)
    # ------------------------------------------------------------------

    async def stream_execute(
        self,
        command: str,
        args: list[str],
        timeout_secs: int | None,
        env: dict[str, str] | None,
        cwd: Path,
        shell: bool = False,
    ):
        """Run a command and yield ``{"stream": …, "text": …}`` dicts.

        The final event carries ``"stream": "exit"`` with exit_code / duration.
        """
        timeout = min(timeout_secs or self.default_timeout, self.max_timeout)

        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        if shell:
            shell_cmd = " ".join([command] + args)
            validate_command(_first_token(shell_cmd), [], self.allowed_commands)
            try:
                process = await asyncio.create_subprocess_exec(
                    "bash",
                    "-c",
                    shell_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                    env=cmd_env,
                )
            except FileNotFoundError:
                yield {
                    "stream": "error",
                    "text": "bash not found (shell mode requires bash)",
                }
                return
        else:
            validate_command(command, args, self.allowed_commands)
            try:
                process = await asyncio.create_subprocess_exec(
                    command,
                    *args,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd),
                    env=cmd_env,
                )
            except FileNotFoundError:
                yield {"stream": "error", "text": f"Command not found: {command}"}
                return

        # -- concurrent readers for stdout / stderr --------------------
        queue: asyncio.Queue[tuple[str | None, str]] = asyncio.Queue()
        readers_alive = 2

        async def _reader(stream, label: str) -> None:
            nonlocal readers_alive
            try:
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    await queue.put((label, line.decode("utf-8", errors="replace")))
            except Exception:
                pass
            finally:
                readers_alive -= 1
                if readers_alive == 0:
                    await queue.put((None, ""))  # sentinel

        stdout_task = asyncio.create_task(_reader(process.stdout, "stdout"))
        stderr_task = asyncio.create_task(_reader(process.stderr, "stderr"))
        start = time.monotonic()
        timed_out = False

        # -- main loop: drain queue until sentinel or timeout ----------
        while True:
            try:
                label, data = await asyncio.wait_for(queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                timed_out = True
                process.kill()
                break

            if label is None:  # sentinel – both readers finished
                break

            yield {"stream": label, "text": data}

        # -- cleanup ---------------------------------------------------
        stdout_task.cancel()
        stderr_task.cancel()

        if not timed_out:
            await process.wait()

        duration = (time.monotonic() - start) * 1000
        yield {
            "stream": "exit",
            "exit_code": process.returncode if not timed_out else -1,
            "duration_ms": round(duration, 2),
            "error": f"Timed out after {timeout}s" if timed_out else None,
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _first_token(cmd: str) -> str:
    """Return the first whitespace-delimited token of a shell command string."""
    return cmd.strip().split()[0] if cmd.strip() else cmd


def _result(
    stdout: str = "",
    stderr: str = "",
    exit_code: int = -1,
    duration_ms: float = 0,
    truncated: bool = False,
    error: str | None = None,
) -> dict:
    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "duration_ms": round(duration_ms, 2),
        "truncated": truncated,
        "error": error,
    }
