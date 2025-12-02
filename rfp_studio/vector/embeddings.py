# rfp_studio/vector/embeddings.py

"""
Embedding utilities for RFP Studio using Voyage-3-Large.

This module centralizes all embedding generation with:
- Voyage-3-Large model for superior performance
- 2048-dimensional embeddings optimized for MongoDB Atlas
- Consistent model choice across the platform
- Batching support for efficiency
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Union
import requests
import json

from rfp_studio.config import get_settings


# ----- Constants -----
VOYAGE_MODEL = "voyage-3-large"
VOYAGE_DIMENSIONS = 2048
VOYAGE_API_URL = "https://api.voyageai.com/v1/embeddings"


# ----- Create Client Once -----

@lru_cache(maxsize=1)
def get_voyage_api_key() -> str:
    """
    Returns the Voyage API key from environment or settings.
    
    Raises immediately if VOYAGE_API_KEY is missing.
    """
    # Check environment first
    api_key = os.getenv("VOYAGE_API_KEY")
    
    if not api_key:
        # Try to get from settings if available
        try:
            settings = get_settings()
            api_key = getattr(settings, 'voyage_api_key', None)
        except:
            pass
    
    if not api_key:
        raise ValueError("VOYAGE_API_KEY must be set for embedding operations.")

    return api_key


# ----- Embedding Functions -----

def embed_text(text: str, model: str = VOYAGE_MODEL) -> List[float]:
    """
    Generate an embedding vector for a single text string using Voyage-3-Large.
    
    Returns 2048-dimensional embedding optimized for MongoDB Atlas Vector Search.
    """
    api_key = get_voyage_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "input": [text],
        "model": model
    }
    
    try:
        response = requests.post(VOYAGE_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        embedding = result["data"][0]["embedding"]
        
        # Verify dimension
        if len(embedding) != VOYAGE_DIMENSIONS:
            raise ValueError(f"Expected {VOYAGE_DIMENSIONS} dimensions, got {len(embedding)}")
        
        return embedding
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Voyage API request failed: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Invalid Voyage API response: {e}")


def embed_many(texts: List[str], model: str = VOYAGE_MODEL) -> List[List[float]]:
    """
    Generate embeddings for multiple text strings using Voyage-3-Large.
    
    Optimized batch processing for better performance.
    """
    if not texts:
        return []
    
    api_key = get_voyage_api_key()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "input": texts,
        "model": model
    }
    
    try:
        response = requests.post(VOYAGE_API_URL, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        embeddings = [item["embedding"] for item in result["data"]]
        
        # Verify dimensions
        for i, embedding in enumerate(embeddings):
            if len(embedding) != VOYAGE_DIMENSIONS:
                raise ValueError(f"Text {i}: Expected {VOYAGE_DIMENSIONS} dimensions, got {len(embedding)}")
        
        return embeddings
    
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Voyage API request failed: {e}")
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        raise RuntimeError(f"Invalid Voyage API response: {e}")


# ----- Compatibility Functions -----

def get_embedding_dimensions() -> int:
    """Return the dimensionality of embeddings."""
    return VOYAGE_DIMENSIONS


def get_embedding_model() -> str:
    """Return the current embedding model name."""
    return VOYAGE_MODEL


# Legacy compatibility (if needed)
get_openai_client = None  # Disable OpenAI client function
