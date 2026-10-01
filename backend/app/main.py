"""FastAPI Application instance for AeroAssist Backend."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes import router

app = FastAPI(
    title="AeroAssist AI Customer Support API",
    description="Enterprise Airline Concierge powered by LangGraph, Neon PostgreSQL, and Google Gemini.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for all frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router under both /api and root /
# Ensures compatibility whether Vercel strips /api or client includes /api
app.include_router(router, prefix="/api")
app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "AeroAssist Backend API (FastAPI)",
        "version": "1.0.0",
        "status": "online",
        "docs": "/docs",
        "health": "/api/health",
    }
