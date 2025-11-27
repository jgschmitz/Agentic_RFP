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
    result: BaseAgentResult = await agent.run(BaseAgentInput(**state))
    return _merge_agent_result(state, result)


async def run_sme_router(state: Dict[str, Any]) -> Dict[str, Any]:
    agent = SMERoutingAgent()
    result: BaseAgentResult = await agent.run(BaseAgentInput(**state))
    return _merge_agent_result(state, result)


# -------- Helpers --------

def _merge_agent_result(prev_state: dict, result: BaseAgentResult) -> dict:
    """
    Merge the agent result into the state passed to the next node.
    """
    new_state = {**prev_state}

    # include changes + events
    new_state.setdefault("agent_changes", []).append(result.changes)
    new_state.setdefault("agent_events", []).append(result.events)

    # set next desired state (workflow)
    if result.next_state:
        new_state["next_state"] = result.next_state

    # propagate success/messaging
    new_state["last_message"] = result.message
    new_state["last_success"] = result.success

    return new_state


def apply_workflow_transition(rfp_id: Optional[str], next_status: Optional[str]):
    """
    Apply workflow status transition to RFP using RFPStatus rules.
    """
    if not rfp_id or not next_status:
        return

    try:
        next_s = RFPStatus(next_status)
    except Exception:
        return

    db = get_db()
    rfp = db.rfps.find_one({"_id": rfp_id})
    if not rfp:
        return

    current_status = rfp.get("status")
    try:
        current_s = RFPStatus(current_status)
    except Exception:
        return

    if can_transition(current_s, next_s):
        db.rfps.update_one(
            {"_id": rfp_id},
            {"$set": {"status": next_s.value}}
        )


# -------- Create the Graph --------

def build_graph():
    graph = StateGraph()

    # Define nodes
    graph.add_node("sales", run_sales_agent)
    graph.add_node("bdm_review", run_bdm_agent)
    graph.add_node("sme_router", run_sme_router)

    # Define edges / flow
    graph.set_entry_point("sales")

    graph.add_edge("sales", "bdm_review")
    graph.add_edge("bdm_review", "sme_router")

    # End after SME routing
    graph.add_edge("sme_router", END)

    return graph.compile()


# -------- Public Entry Point --------

async def run_flow(
    rfp_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Run the full Sales → BDM → SME Routing workflow.

    You can override the graph or call individual nodes
    if you want partial workflows.
    """

    graph = build_graph()

    initial_state = {
        "rfp_id": rfp_id,
        "payload": payload or {},
        "context": context or {},
    }

    final_state = await graph.ainvoke(initial_state)

    # Apply workflow transitions if provided
    if "next_state" in final_state and rfp_id:
        apply_workflow_transition(rfp_id, final_state.get("
