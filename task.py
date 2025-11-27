# rfp_studio/models/task.py

"""
Task models for RFP Studio.

Tasks represent unit work items in the RFP workflow:
- SME questions
- Writer drafting steps
- Legal review items
- Quality checks
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class TaskType(str, Enum):
    SALES_INTAKE = "SALES_INTAKE"
    BDM_REVIEW = "BDM_REVIEW"
    RFP_BREAKDOWN = "RFP_BREAKDOWN"
    SME_QA = "SME_QA"
    SME_ANSWER = "SME_ANSWER"
    CONTENT_DRAFT = "CONTENT_DRAFT"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    QUALITY_REVIEW = "QUALITY_REVIEW"
    VP_APPROVAL = "VP_APPROVAL"
    SUBMISSION = "SUBMISSION"
    OTHER = "OTHER"


class Task(BaseModel):
    """
    Generic workflow task.

    These are typically embedded under RFP.tasks but can also be stored
    in a separate `tasks` collection if you want a global task view.
    """

    # Identity
    id: Optional[str] = None           # when stored as its own document
    rfp_id: Optional[str] = None       # parent RFP (string ObjectId)

    # Classification
    type: TaskType = TaskType.OTHER
    status: TaskStatus = TaskStatus.PENDING

    # Ownership
    assigned_to_user_id: Optional[str] = None
    assigned_to_team: Optional[str] = None   # e.g. "sme_team_security"
    agent_type: Optional[str] = None         # e.g. "SME_ROUTING_AGENT"

    # Content / payload
    title: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Timeline
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    due_at: Optional[str] = None

    # Optional vector context (for SME routing, answer reuse, etc.)
    embedding: Optional[List[float]] = None
