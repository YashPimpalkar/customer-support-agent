"""Configuration module for the AeroAssist Backend.

Loads environment variables from .env and configures the LLM model.
"""

from __future__ import annotations

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent
PROJECT_ROOT = BACKEND_DIR.parent
BOT_ROOT = Path("/home/client/langraph/customer_support_bot")

# Priority loading: backend/.env -> project_root/.env -> bot_root/.env
if (BACKEND_DIR / ".env").exists():
    load_dotenv(BACKEND_DIR / ".env", override=True)
elif (PROJECT_ROOT / ".env").exists():
    load_dotenv(PROJECT_ROOT / ".env", override=False)
elif (BOT_ROOT / ".env").exists():
    load_dotenv(BOT_ROOT / ".env", override=False)

# Neon PostgreSQL connection string
DEFAULT_DATABASE_URL = (
    "postgresql://neondb_owner:npg_2Mb1dzZxHrmw@ep-fancy-king-b4pflhay-pooler.c-6.us-east-2.aws.neon.tech/customer_support_agent?sslmode=require&channel_binding=require"
)

env_db_url = os.environ.get("NEON_DATABASE_URL") or os.environ.get("CUSTOMER_SUPPORT_DB_URL")
if not env_db_url:
    raw_url = os.environ.get("DATABASE_URL", "")
    if "neon.tech" in raw_url:
        env_db_url = raw_url
    else:
        env_db_url = DEFAULT_DATABASE_URL

DATABASE_URL: str = env_db_url

GOOGLE_API_KEY: str = os.environ.get("GOOGLE_API_KEY", "")
raw_model = os.environ.get("GOOGLE_MODEL", "gemini-3.1-flash-lite")
if raw_model in ("3.1", "gemini-3.1", "gemini-3.1-flash", "gemini-3.8-flash"):
    raw_model = "gemini-3.1-flash-lite"
GOOGLE_MODEL: str = raw_model
GOOGLE_EMBEDDING_MODEL: str = os.environ.get("GOOGLE_EMBEDDING_MODEL", "text-embedding-004")

# Policies documentation file
POLICY_PATH = APP_DIR / "rag" / "policies.md"
if not POLICY_PATH.exists():
    POLICY_PATH = BACKEND_DIR / "policies.md"


def get_llm(temperature: float = 0.3):
    """Factory function for initializing Gemini Chat Model with LangChain."""
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=GOOGLE_MODEL,
        temperature=temperature,
        google_api_key=GOOGLE_API_KEY,
        max_retries=1,
    )
