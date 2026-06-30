from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.responses import RedirectResponse

from app.api.router import api_router
from app.core.auth import auth_middleware
from app.core.config import Settings
from app.core.executor import Executor
from app.core.workspace import WorkspaceManager


def create_app(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        settings = Settings()

    servers = [{"url": settings.domain}] if settings.domain else None

    app = FastAPI(
        title="Shell Server",
        description="A RESTful API for executing shell commands in a sandboxed "
        "workspace. Commands are restricted to the workspace directory "
        "and protected by timeouts, output limits, and optional "
        "command whitelisting.",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        servers=servers,
    )

    # -- store settings on app state for easy access -------------------
    app.state.settings = settings

    # -- OpenAPI security scheme ----------------------------------------
    if settings.auth_token:
        _add_bearer_security(app)

    # -- workspace & executor ------------------------------------------
    workspace = WorkspaceManager(Path(settings.workspace_path))
    executor = Executor(
        allowed_commands=settings.allowed_commands,
        max_output_size=settings.max_output_size,
        default_timeout=settings.default_timeout,
        max_timeout=settings.max_timeout,
    )

    app.state.workspace = workspace
    app.state.executor = executor

    # -- auth middleware -------------------------------------------------
    if settings.auth_token:
        app.middleware("http")(auth_middleware(settings.auth_token))

    # -- lifespan ------------------------------------------------------
    @app.on_event("startup")
    async def on_startup():
        # Ensure workspace exists at startup
        workspace.root.mkdir(parents=True, exist_ok=True)

    # -- routes --------------------------------------------------------
    app.include_router(api_router)

    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    return app


def _add_bearer_security(app: FastAPI) -> None:
    """Inject Bearer token security scheme into the OpenAPI schema."""
    original_openapi = app.openapi

    def patched_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        schema = get_openapi(
            title=app.title,
            version=app.version,
            openapi_version=app.openapi_version,
            description=app.description,
            routes=app.routes,
            servers=app.servers,
        )
        schema.setdefault("components", {}).setdefault("securitySchemes", {})
        schema["components"]["securitySchemes"]["BearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "API token",
            "description": "Enter your API token. Requests without a valid "
            "token return 401/403.",
        }
        schema.setdefault("security", [])
        schema["security"].append({"BearerAuth": []})
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = patched_openapi


# ---------------------------------------------------------------------------
# Entry point (used by:  uvicorn app.main:app)
# ---------------------------------------------------------------------------
app = create_app()
