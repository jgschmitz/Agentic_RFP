# rfp_studio/vector/embeddings.py

"""
Embedding utilities for RFP Studio.

This module centralizes all embedding generation so:
- Agents do not instantiate OpenAI clients directly
- Model choice is consistent
- Batching becomes possible later
"""

from __future__ import annotations

from functools import lru_cache
from typing import List, Union

from openai import OpenAI
from rfp_studio.config import get_settings


# ----- Constants -----
DEFAULT_EMBED_MODEL = "text-embedding-3-small"


# ----- Create Client Once -----

@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    """
    Returns a cached OpenAI client.

    Raises immediately if OPENAI_API_KEY is missing.
    """
    settings = get_settings()
    if not settings.openai_api_key:
        raise ValueError("OPENAI_API_KEY must be set for embedding operations.")

    return OpenAI(api_key=settings.openai_api_key)


# ----- Embedding Functions -----

def embed_text(text: str, model: str = DEFAULT_EMBED_MODEL) -> List[float]:
    """
    Generate an embedding vector for a single text string.
    """
    client = get_openai_client()
    resp = client.embeddings.create(
        model=model,
        input=text,
    )
    return resp.data[0].embedding


def embed_many(texts: List[str], model: str = DEFAULT_EMBED_MODEL) -> List[List[float]]:
    """
    Generate embeddings for multiple text strings.

    Optimized future: batch calls, async.
    """
    client = get_openai_client()
    resp = client.embeddings.create(
        model=model,
        input=texts,
    )
    return [item.embedding for item in resp.data]
