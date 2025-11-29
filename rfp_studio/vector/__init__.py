# rfp_studio/vector/__init__.py

"""
Vector search package for RFP Studio.

Contains embeddings generation and Atlas Vector Search utilities.
"""

from .embeddings import embed_text, embed_many, get_openai_client
from .atlas_query import vector_search, search_knowledge_base, search_rfps

__all__ = [
    "embed_text",
    "embed_many", 
    "get_openai_client",
    "vector_search",
    "search_knowledge_base",
    "search_rfps",
]