"""Command line execution entrypoint for backend.app with Uvicorn."""

from __future__ import annotations

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() in ("true", "1", "t")
    uvicorn.run("app.main:app", host=host, port=port, reload=reload)
