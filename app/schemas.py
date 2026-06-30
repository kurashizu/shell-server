from __future__ import annotations

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class ExecRequest(BaseModel):
    command: str = Field(
        ..., description="Command to execute (e.g. ``ls``, ``python``)"
    )
    args: list[str] = Field(default=[], description="Arguments passed to the command")
    timeout_secs: int | None = Field(
        default=None,
        description="Timeout in seconds (defaults to server default, capped at server max)",
        ge=1,
        le=300,
    )
    env: dict[str, str] = Field(
        default={},
        description="Additional environment variables to set for this invocation",
    )


class ExecStreamRequest(BaseModel):
    """Same as ExecRequest but for the streaming endpoint."""

    command: str = Field(
        ..., description="Command to execute (e.g. ``ls``, ``python``)"
    )
    args: list[str] = Field(default=[], description="Arguments passed to the command")
    timeout_secs: int | None = Field(
        default=None,
        description="Timeout in seconds",
        ge=1,
        le=300,
    )
    env: dict[str, str] = Field(
        default={},
        description="Additional environment variables",
    )


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class ExecResponse(BaseModel):
    stdout: str = Field(..., description="Standard output")
    stderr: str = Field(..., description="Standard error")
    exit_code: int = Field(
        ..., description="Exit code (-1 if timed out or command not found)"
    )
    duration_ms: float = Field(..., description="Execution duration in milliseconds")
    truncated: bool = Field(
        default=False,
        description="Whether the output was truncated due to size limits",
    )
    error: str | None = Field(
        default=None,
        description="Error message if the command timed out or was not found",
    )


class FileInfo(BaseModel):
    name: str = Field(..., description="File or directory name")
    path: str = Field(..., description="Relative path from workspace root")
    type: str = Field(..., description="``file`` or ``dir``")
    size: int = Field(..., description="File size in bytes (0 for directories)")


class WorkspaceListResponse(BaseModel):
    files: list[FileInfo] = Field(
        ..., description="Files and directories in the workspace"
    )


class WorkspaceResetResponse(BaseModel):
    message: str = Field(..., description="Status message")
