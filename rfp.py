# rfp_studio/models/rfp.py

"""
Pydantic models for RFP documents stored in MongoDB Atlas.

These models define:
- The structured RFP record
- Validation for incoming agent updates
- Clean data objects used throughout the workflow
"""

from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


# ---------- Sub-Models ----------

class ClientInfo(BaseModel):
    name: str
    contact: Optional[str] = None


class Timeline(BaseModel):
    received_date: Optional[str] = None
    due_date: Optional[str] = None
    milestones: List[Dict[str, Any]] = Field(default_factory=list)


class Participants(BaseModel):
    sales_team: List[str] = Field(default_factory=list)
    bdm: Optional[str] = None
    writers: List[str] = Field(default_factory=list)
    smes: List[str] = Field(default_factory=list)


class DocumentLinks(BaseModel):
    original_rfp_url: Optional[str] = None
    draft_document_url: Optional[str] = None
    final_document_url: Optional[str] = None


class Metadata(BaseModel):
    industry: Optional[str] = None
    rfp_size: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


# ---------- Main RFP Model ----------

class RFP(BaseModel):
    """
    Core RFP document schema.

    Mirrors the design architecture:
    - RFPs are structured MongoDB documents
    - Agents update individual fields
    - Vector search and triggers operate over clean objects
    """

    title: str
    client: ClientInfo
    status: str = "INITIATED"

    timeline: Timeline = Timeline()
    participants: Participants = Participants()

    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    documents: DocumentLinks = DocumentLinks()
    history: List[Dict[str, Any]] = Field(default_factory=list)

    metadata: Metadata = Metadata()

    # Optional: embedded vector embeddings (for similarity search)
    embedding: Optional[List[float]] = None


# ---------- Serialization Helpers ----------

def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB document → API/agent friendly dict.
    - Renames _id → id
    """
    if not doc:
        return doc
    clean = {**doc}
    clean["id"] = str(clean.pop("_id"))
    return clean
