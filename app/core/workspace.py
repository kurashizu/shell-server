from __future__ import annotations

import shutil
from pathlib import Path

from .jail import SecurityError, validate_path


class WorkspaceManager:
    """Manages the sandboxed workspace directory."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def reset(self) -> None:
        """Delete and recreate the workspace directory."""
        if self.root.exists():
            shutil.rmtree(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_files(self, subpath: str = "") -> list[dict]:
        """List entries in a workspace subpath."""
        target = validate_path(self.root, subpath) if subpath else self.root
        if not target.exists():
            raise SecurityError(f"Path does not exist: {subpath}")
        if not target.is_dir():
            raise SecurityError(f"Not a directory: {subpath}")

        results: list[dict] = []
        for entry in sorted(target.iterdir()):
            rel = entry.relative_to(self.root)
            results.append(
                {
                    "name": entry.name,
                    "path": str(rel),
                    "type": "dir" if entry.is_dir() else "file",
                    "size": entry.stat().st_size if entry.is_file() else 0,
                }
            )
        return results

    def read_file(self, filepath: str) -> bytes:
        """Read raw bytes from a file in the workspace."""
        target = validate_path(self.root, filepath)
        if not target.is_file():
            raise SecurityError(f"Not a file or not found: {filepath}")
        return target.read_bytes()

    def write_file(self, filepath: str, content: bytes) -> None:
        """Write raw bytes to a file in the workspace."""
        target = validate_path(self.root, filepath)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def delete_path(self, filepath: str) -> None:
        """Delete a file or empty directory from the workspace."""
        target = validate_path(self.root, filepath)
        if not target.exists():
            raise SecurityError(f"Path not found: {filepath}")
        if target == self.root:
            raise SecurityError("Cannot delete workspace root")
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()
