#!/usr/bin/env python
"""Entry point that reads Settings from .env / env vars and starts uvicorn.

Usage:
    python run.py            # production
    python run.py --reload   # development (auto-reload on file changes)
"""

from __future__ import annotations

import sys

import uvicorn
from app.core.config import Settings


def main() -> None:
    settings = Settings()
    reload = "--reload" in sys.argv

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=reload,
    )


if __name__ == "__main__":
    main()
