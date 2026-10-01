"""Root ASGI and CLI entrypoint for AeroAssist customer_support_app."""

from __future__ import annotations

import os
import sys
from pathlib import Path
import uvicorn

# Ensure the project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app

__all__ = ["app"]


def main():
    """Launch the AeroAssist FastAPI application via Uvicorn."""
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() in ("true", "1", "t")
    print(f"🚀 Starting AeroAssist Backend on http://{host}:{port} (reload={reload})")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()
