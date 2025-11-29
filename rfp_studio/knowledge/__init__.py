# rfp_studio/knowledge/__init__.py

"""
Knowledge management package for RFP Studio.

Contains utilities for loading and managing the knowledge base.
"""

from .loader import KnowledgeItem, load_knowledge_items, load_sample_knowledge, clear_knowledge_base

__all__ = [
    "KnowledgeItem",
    "load_knowledge_items", 
    "load_sample_knowledge",
    "clear_knowledge_base",
]