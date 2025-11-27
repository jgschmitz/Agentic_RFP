# rfp_studio/knowledge/loader.py

"""
Knowledge base loader for RFP Studio.

Responsibilities:
- Ingest knowledge items (Q&A, docs, prior RFP snippets)
- Generate embeddings for each item
- Store them in the `knowledge_base` collection in MongoDB Atlas

Intended usage:
- One-off scripts to seed KB
- Maintenance tasks to refresh / add new content
- Supports SME routing via `team_key`
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from bson import ObjectId

from rfp_studio.db.atlas import get_db
from rfp_studio.vector.embeddings import embed_many


@dataclass
class KnowledgeItem:
    """
    In-memory representation of a single KB item.

    Fields:
        text: The text content used for embedding/search.
        team_key: Logical SME team owner, e.g. "sme_team_security".
        topic: Optional short label, e.g. "SOC2", "SLA", "Pricing".
        tags: Optional list of tags, e.g. ["security", "compliance"].
        extra: Arbitrary payload stored as-is in the document.
    """

    text: str
    team_key: str
    topic: Optional[str] = None
    tags: Optional[List[str]] = None
    extra: Optional[Dict[str, Any]] = None


def _to_document(item: KnowledgeItem, embedding: List[float]) -> Dict[str, Any]:
    now_iso = datetime.utcnow().isoformat()
    doc: Dict[str, Any] = {
        "text": item.text,
        "team_key": item.team_key,
        "embedding": embedding,
        "created_at": now_iso,
        "updated_at": now_iso,
    }

    if item.topic is not None:
        doc["topic"] = item
