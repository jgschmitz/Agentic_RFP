# rfp_studio/workflow/states.py

"""
Workflow states and transitions for RFP Studio.

This reflects the architecture notes:

INITIATED → LINKED_TO_RFP → SALES_ASSEMBLY → BDM_REVIEW → RFP_BREAKDOWN
→ SME_QA → CONTENT_DRAFT → LEGAL_REVIEW → QUALITY_REVIEW → FINAL_RFP
→ APPROVED_BY_VP → SUBMISSION_READY → SUBMITTED
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List


class RFPStatus(str, Enum):
    INITIATED = "INITIATED"
    LINKED_TO_RFP = "LINKED_TO_RFP"
    SALES_ASSEMBLY = "SALES_ASSEMBLY"
    BDM_REVIEW = "BDM_REVIEW"
    RFP_BREAKDOWN = "RFP_BREAKDOWN"
    SME_QA = "SME_QA"
    CONTENT_DRAFT = "CONTENT_DRAFT"
    LEGAL_REVIEW = "LEGAL_REVIEW"
    QUALITY_REVIEW = "QUALITY_REVIEW"
    FINAL_RFP = "FINAL_RFP"
    APPROVED_BY_VP = "APPROVED_BY_VP"
    SUBMISSION_READY = "SUBMISSION_READY"
    SUBMITTED = "SUBMITTED"


# Allowed transitions as a simple adjacency map
ALLOWED_TRANSITIONS: Dict[RFPStatus, List[RFPStatus]] = {
    RFPStatus.INITIATED: [RFPStatus.LINKED_TO_RFP],
    RFPStatus.LINKED_TO_RFP: [RFPStatus.SALES_ASSEMBLY],
    RFPStatus.SALES_ASSEMBLY: [RFPStatus.BDM_REVIEW],
    RFPStatus.BDM_REVIEW: [RFPStatus.RFP_BREAKDOWN],
    RFPStatus.RFP_BREAKDOWN: [RFPStatus.SME_QA],
    RFPStatus.SME_QA: [RFPStatus.CONTENT_DRAFT],
    RFPStatus.CONTENT_DRAFT: [RFPStatus.LEGAL_REVIEW],
    RFPStatus.LEGAL_REVIEW: [RFPStatus.QUALITY_REVIEW],
    RFPStatus.QUALITY_REVIEW: [RFPStatus.FINAL_RFP],
    RFPStatus.FINAL_RFP: [RFPStatus.APPROVED_BY_VP],
    RFPStatus.APPROVED_BY_VP: [RFPStatus.SUBMISSION_READY],
    RFPStatus.SUBMISSION_READY: [RFPStatus.SUBMITTED],
    RFPStatus.SUBMITTED: [],
}


def can_transition(from_status: RFPStatus, to_status: RFPStatus) -> bool:
    """
    Return True if workflow is allowed to move from from_status → to_status.
    """
    return to_status in ALLOWED_TRANSITIONS.get(from_status, [])


def get_next_valid_states(from_status: RFPStatus) -> list[RFPStatus]:
    """
    Convenience helper for agents to see next legal states.
    """
    return ALLOWED_TRANSITIONS.get(from_status, [])
