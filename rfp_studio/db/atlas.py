# rfp_studio/db/atlas.py

"""
MongoDB Atlas connection for RFP Studio.

This module does ONLY:
- Create a single MongoDB client
- Provide access to the configured database

No wrappers, no ORM, no custom helpers.
"""

from __future__ import annotations

from pymongo import MongoClient
from rfp_studio.config import get_settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    """
    Returns a singleton MongoDB Atlas client.
    """
    global _client
    if _client is None:
        settings = get_settings()
        _client = MongoClient(settings.mongodb_uri)
    return _client


def get_db():
    """
    Get the Atlas database specified in config.
    """
    settings = get_settings()
    return get_client()[settings.mongodb_db_name]
