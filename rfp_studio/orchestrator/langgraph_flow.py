# rfp_studio/orchestrator/langgraph_flow.py

"""
LangGraph orchestrator for RFP Studio.

This is the high-level workflow engine that:
- Wires all agents together as a graph
- Defines routing logic between agents
- Applies workflow state transitions
- Provides a single `run_flow()` entrypoint

This is deliberately minimal but production-ready.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from rfp_studio.agents.sales import SalesAgent
from rfp_studio.agents.bdm import BDMReviewAgent
from rfp_studio.agents.sme_router import SMERoutingAgent
from rfp_studio.agents.base import BaseAgentInput, BaseAgentResult
from rfp_studio.workflow.states import (
    RFPStatus,
    can_transition,
)
from rfp_studio.db.atlas import get_db


# -------- Graph Node Wrappers --------

async def run_sales_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = SalesAgent()
    result: BaseAgentResult = await agent.run(BaseAgentInput(**state))
    return _merge_agent_result(state, result)


async def run_bdm_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = BDMReviewAgent()
    result: Ba
