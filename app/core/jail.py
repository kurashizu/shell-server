from __future__ import annotations

import os
from pathlib import Path


class SecurityError(Exception):
    """Raised when a security check fails."""

    pass


def validate_path(workspace_root: Path, requested_path: str) -> Path:
    """Resolve a path relative to workspace_root and ensure it stays inside.

    Args:
        workspace_root: The absolute path to the workspace.
        requested_path: A relative path from the user request.

    Returns:
        The resolved absolute Path within the workspace.

    Raises:
        SecurityError: If the resolved path escapes the workspace.
    """
    resolved = (workspace_root / requested_path).resolve()
    root_str = str(workspace_root.resolve())

    if (
        not str(resolved).startswith(root_str + os.sep)
        and resolved != workspace_root.resolve()
    ):
        raise SecurityError(f"Path traversal detected: {requested_path}")

    return resolved


def validate_command(
    command: str, args: list[str], allowed_commands: list[str]
) -> None:
    """Check a command against the whitelist (if configured).

    Args:
        command: The command to check.
        args: Command arguments (unused in validation, kept for future use).
        allowed_commands: List of allowed commands. Empty = allow all.

    Raises:
        SecurityError: If the command is not in the whitelist.
    """
    if not allowed_commands:
        return
    if command not in allowed_commands:
        raise SecurityError(
            f"Command '{command}' is not allowed. "
            f"Allowed: {', '.join(sorted(allowed_commands))}"
        )
