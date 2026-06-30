from __future__ import annotations

from fastapi import HTTPException, Request
from starlette.responses import JSONResponse
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN


def auth_middleware(auth_token: str | None):
    """Create a middleware that enforces Bearer token authentication.

    Skips checks when ``auth_token`` is empty (no auth required).
    Docs endpoints are always allowed.
    """

    async def middleware(request: Request, call_next):
        if not auth_token:
            return await call_next(request)

        # Allow docs endpoints and OPTIONS preflight
        path = request.url.path
        if path in ("/docs", "/redoc", "/openapi.json") or request.method == "OPTIONS":
            return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=HTTP_401_UNAUTHORIZED,
                content={
                    "detail": "Missing or malformed Authorization header. "
                    "Expected: Authorization: Bearer <token>"
                },
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.removeprefix("Bearer ").strip()
        if token != auth_token:
            return JSONResponse(
                status_code=HTTP_403_FORBIDDEN,
                content={"detail": "Invalid token"},
            )

        return await call_next(request)

    return middleware
