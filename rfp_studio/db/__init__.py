# rfp_studio/db/__init__.py

"""
Database package for RFP Studio.

Contains MongoDB Atlas connection and utilities.
"""

from .atlas import get_client, get_db

__all__ = [
    "get_client",
    "get_db",
]