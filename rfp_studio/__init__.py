# rfp_studio/__init__.py

"""
RFP Studio - AI-orchestrated RFP automation platform.

Main entry point for the RFP Studio package.
"""

from .agents import SalesAgent, BDMReviewAgent, SMERoutingAgent
from .models.rfp import RFP, ClientInfo, Timeline, Participants, DocumentLinks, Metadata
from .models.task import Task, TaskStatus, TaskType
from .orchestrator.langgraph_flow import run_flow, run_sales_only, run_bdm_only, run_sme_router_only
from .config import get_settings

__version__ = "0.1.0"
__author__ = "RFP Studio Team"
__description__ = "AI-orchestrated RFP automation platform powered by Python, LangGraph, and MongoDB Atlas"

__all__ = [
    # Core agents
    "SalesAgent",
    "BDMReviewAgent", 
    "SMERoutingAgent",
    # Models
    "RFP",
    "ClientInfo",
    "Timeline",
    "Participants", 
    "DocumentLinks",
    "Metadata",
    "Task",
    "TaskStatus",
    "TaskType",
    # Orchestration
    "run_flow",
    "run_sales_only",
    "run_bdm_only", 
    "run_sme_router_only",
    # Configuration
    "get_settings",
]