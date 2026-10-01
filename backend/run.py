"""Entrypoint to launch the AeroAssist backend server with Uvicorn."""

from __future__ import annotations

import os
import sys
from pathlib import Path
import uvicorn

# Ensure customer_support_app root is in sys.path
root_dir = str(Path(__file__).resolve().parent.parent)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    host = os.environ.get("HOST", "0.0.0.0")
    reload = os.environ.get("RELOAD", "True").lower() in ("true", "1", "t")
    print(f"Starting AeroAssist FastAPI Backend on http://{host}:{port} with Uvicorn (reload={reload})")
    uvicorn.run("backend.app.main:app", host=host, port=port, reload=reload)
