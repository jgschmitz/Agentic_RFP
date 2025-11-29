# rfp_studio/config.py

"""
Central configuration for RFP Studio.

- Reads environment variables (optionally from a .env file)
- Provides a single Settings object for the rest of the codebase
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional, List

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator

# Load variables from .env if present
load_dotenv()


class Settings(BaseModel):
    """
    Configuration container for RFP Studio.

    Values are typically supplied via environment variables:

    - MONGODB_URI
    - MONGODB_DB_NAME
    - OPENAI_API_KEY
    - ATLAS_VECTOR_INDEX_RFPS
    - ATLAS_VECTOR_INDEX_KB
    - RFP_STUDIO_ENV
    """

    mongodb_uri: str
    mongodb_db_name: str = "rfp_studio"

    # LLM / embeddings (optional but recommended)
    openai_api_key: Optional[str] = None

    # Atlas Vector Search index names
    atlas_vector_index_rfps: str = "rfp_vector_index"
    atlas_vector_index_kb: str = "kb_vector_index"

    # dev / staging / prod, etc.
    env: str = "development"

    @field_validator("mongodb_uri")
    @classmethod
    def validate_mongodb_uri(cls, v: str) -> str:
        if not v:
            raise ValueError("MONGODB_URI must be set")
        if not v.startswith("mongodb://") and not v.startswith("mongodb+srv://"):
            raise ValueError("MONGODB_URI must start with mongodb:// or mongodb+srv://")
        return v

    @classmethod
    def from_env(cls) -> "Settings":
        """
        Build a Settings object from environment variables.
        """
        return cls(
            mongodb_uri=os.getenv("MONGODB_URI", ""),
            mongodb_db_name=os.getenv("MONGODB_DB_NAME", "rfp_studio"),
            openai_api_key=os.getenv("OPENAI_API_KEY") or None,
            atlas_vector_index_rfps=os.getenv(
                "ATLAS_VECTOR_INDEX_RFPS", "rfp_vector_index"
            ),
            atlas_vector_index_kb=os.getenv(
                "ATLAS_VECTOR_INDEX_KB", "kb_vector_index"
            ),
            env=os.getenv("RFP_STUDIO_ENV", "development"),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Cached access to Settings.

    Usage:
        from rfp_studio.config import get_settings
        settings = get_settings()
    """
    return Settings.from_env()
