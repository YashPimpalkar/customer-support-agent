"""FastAPI application entrypoint for Vercel deployment inside backend directory."""

from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = str(Path(__file__).resolve().parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app

__all__ = ["app"]
