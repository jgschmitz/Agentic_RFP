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
        doc["topic"] = item.topic

    if item.tags is not None:
        doc["tags"] = item.tags

    if item.extra is not None:
        doc.update(item.extra)

    return doc


def load_knowledge_items(items: List[KnowledgeItem]) -> List[str]:
    """
    Load knowledge items into MongoDB Atlas.

    Steps:
    1. Generate embeddings for all items in batch
    2. Store documents in the `knowledge_base` collection
    3. Return list of inserted ObjectIds as strings

    Args:
        items: List of KnowledgeItem objects to load

    Returns:
        List of inserted document IDs (as strings)
    """
    if not items:
        return []

    db = get_db()
    collection = db["knowledge_base"]

    # Extract text for batch embedding
    texts = [item.text for item in items]

    # Generate embeddings in batch for efficiency
    embeddings = embed_many(texts)

    # Convert to MongoDB documents
    documents = [
        _to_document(item, embedding)
        for item, embedding in zip(items, embeddings)
    ]

    # Insert into MongoDB
    result = collection.insert_many(documents)
    return [str(oid) for oid in result.inserted_ids]


def load_sample_knowledge() -> List[str]:
    """
    Load sample knowledge items for testing/demo purposes.

    This creates a basic knowledge base with common RFP areas.
    """
    sample_items = [
        KnowledgeItem(
            text="Our company provides enterprise security consulting including SOC2, HIPAA, and PCI compliance auditing.",
            team_key="sme_team_security",
            topic="Security & Compliance",
            tags=["security", "compliance", "audit"]
        ),
        KnowledgeItem(
            text="We offer 24/7 technical support with guaranteed response times of 4 hours for critical issues.",
            team_key="sme_team_support",
            topic="Support & SLA",
            tags=["support", "sla", "response_time"]
        ),
        KnowledgeItem(
            text="Our pricing model is based on monthly subscription tiers with enterprise volume discounts available.",
            team_key="sme_team_sales",
            topic="Pricing & Licensing",
            tags=["pricing", "licensing", "subscription"]
        ),
        KnowledgeItem(
            text="Technical implementation includes API integration, data migration services, and custom configuration.",
            team_key="sme_team_technical",
            topic="Technical Implementation",
            tags=["api", "integration", "migration"]
        ),
        KnowledgeItem(
            text="Our legal team handles contract negotiations, terms of service, and data protection agreements.",
            team_key="sme_team_legal",
            topic="Legal & Contracts",
            tags=["legal", "contracts", "data_protection"]
        ),
    ]

    return load_knowledge_items(sample_items)


def clear_knowledge_base() -> int:
    """
    Clear all items from the knowledge base collection.
    
    Returns:
        Number of documents deleted
    """
    db = get_db()
    collection = db["knowledge_base"]
    result = collection.delete_many({})
    return result.deleted_count


if __name__ == "__main__":
    # Example usage for command-line loading
    print("Loading sample knowledge base...")
    inserted_ids = load_sample_knowledge()
    print(f"Successfully loaded {len(inserted_ids)} knowledge items.")
    print(f"Inserted IDs: {inserted_ids}")
