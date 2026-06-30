from __future__ import annotations

import json
import os
from typing import Any, Tuple, Type

from pydantic import Field, field_validator
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


class _LenientEnvSource(EnvSettingsSource):
    """Env source that doesn't crash on non-JSON strings for complex fields.

    The default EnvSettingsSource tries ``json.loads()`` on complex-typed
    fields (e.g. ``list[str]``) and raises if it fails.  This version
    returns the raw string instead so that downstream validators can
    handle comma-separated values.
    """

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: str, value_is_complex: bool
    ) -> Any:
        if value_is_complex and isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, ValueError):
                return value  # let validators deal with it
        return value


class Settings(BaseSettings):
    # Server
    host: str = "127.0.0.1"
    port: int = 8080

    # Workspace
    workspace_path: str = "/tmp/shell-server-workspace"

    # Execution limits
    default_timeout: int = 30  # seconds
    max_timeout: int = 300  # seconds
    max_output_size: int = 1_048_576  # 1 MB

    # Security
    allowed_commands: list[str] = Field(
        default=[],
        description="List of allowed commands (comma-separated or JSON array)",
    )
    auth_token: str | None = Field(
        default=None, description="Bearer token for authentication (empty = no auth)"
    )

    model_config = SettingsConfigDict(
        env_prefix="SHELL_SERVER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -- custom parsing for allowed_commands --------------------------------

    @field_validator("allowed_commands", mode="before")
    @classmethod
    def parse_allowed_commands(cls, v: object) -> list[str]:
        return cls._parse_allowed_commands(v)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            _LenientEnvSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    @classmethod
    def _parse_allowed_commands(cls, v: object) -> list[str]:
        """Convert a raw string or list into a list of command names."""
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            # Try JSON array first
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    pass
            # Fall back to comma / whitespace split
            return [cmd.strip() for cmd in v.replace(",", " ").split()]
        return []
