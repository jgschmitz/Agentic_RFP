# rfp_studio/vector/atlas_query.py

"""
MongoDB Atlas Vector Search helpers for RFP Studio.

This module provides small, focused helpers around the $vectorSearch stage.

Core concepts:
- We always use Atlas' native $vectorSearch aggregation stage.
- We do NOT wrap MongoDB collections; we just help build pipelines.
- Agents and orchestrators call these helpers to keep pipelines consistent.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from rfp_studio.db.atlas import get_db
from rfp_studio.config import get_settings


def vector_search(
    collection_name: str,
    index_name: str,
    query_vector: List[float],
    path: str = "embedding",
    limit: int = 5,
    num_candidates: int = 200,
    filter: Optional[Dict[str, Any]] = None,
    projection: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generic Atlas Vector Search helper.

    Arguments:
        collection_name: MongoDB collection name (e.g. "knowledge_base").
        index_name: Atlas Vector Search index name.
        query_vector: The embedding vector to search with.
        path: The field containing the vector in the collection (default: "embedding").
        limit: Top-K results.
        num_candidates: Candidate pool size for vector search.
        filter: Optional additional filter document.
        projection: Optional $project document.

    Returns:
        List of result documents.
    """
    db = get_db()
    collection = db[collection_name]

    vector_stage: Dict[str, Any] = {
        "$vectorSearch": {
            "index": index_name,
            "queryVector": query_vector,
            "path": path,
            "numCandidates": num_candidates,
            "limit": limit,
        }
    }
    if filter:
        vector_stage["$vectorSearch"]["filter"] = filter

    pipeline: List[Dict[str, Any]] = [vector_stage]

    if projection:
        pipeline.append({"$project": projection})

    # Make sure we don't accidentally return more than requested
    pipeline.append({"$limit": limit})

    return list(collection.aggregate(pipeline))


def search_knowledge_base(
    query_vector: List[float],
    limit: int = 5,
    filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Vector search over the `knowledge_base` collection.

    Documents are expected to have:
    - embedding: list[float]
    - team_key: str (for SME routing)
    - optionally topic/tags/etc.
    """
    settings = get_settings()
    projection = {
        "_id": 1,
        "team_key": 1,
        "topic": 1,
        "tags": 1,
        "score": {"$meta": "vectorSearchScore"},
    }

    return vector_search(
        collection_name="knowledge_base",
        index_name=settings.atlas_vector_index_kb,
        query_vector=query_vector,
        path="embedding",
        limit=limit,
        num_candidates=200,
        filter=filter,
        projection=projection,
    )


def search_rfps(
    query_vector: List[float],
    limit: int = 5,
    filter: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Vector search over the `rfps` collection.

    Use cases:
    - Find similar RFPs by title/summary.
    - Power "similar RFP lookup" for writers / analysts.
    """
    settings = get_settings()
    projection = {
        "_id": 1,
        "title": 1,
        "client": 1,
        "metadata": 1,
        "status": 1,
        "score": {"$meta": "vectorSearchScore"},
    }

    return vector_search(
        collection_name="rfps",
        index_name=settings.atlas_vector_index_rfps,
        query_vector=query_vector,
        path="embedding",
        limit=limit,
        num_candidates=200,
        filter=filter,
        projection=projection,
    )
