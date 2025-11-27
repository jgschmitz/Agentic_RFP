# rfp_studio/agents/base.py

"""
Base agent interfaces for RFP Studio.

Each concrete agent (Sales, BDM, SME Router, Writer, Legal, Quality, etc.)
should inherit from BaseAgent and implement the `run()` method.

This keeps:
- IO contracts explicit
- Agent types discoverable
- Orchestrator logic clean
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class BaseAgentConfig(BaseModel):
    """
    Configuration / identity for an agent.
    """

    name: str
    description: str
    agent_type: str = Field(
        default="GENERIC_AGENT",
        description="Logical type (e.g. SALES_AGENT, BDM_AGENT, SME_ROUTING_AGENT)",
    )


class BaseAgentInput(BaseModel):
    """
    Shared input contract for agents.

    This is intentionally generic:
    - rfp_id: target RFP in MongoDB
    - payload: agent-specific data (question, section text, etc.)
    - context: optional orchestration metadata
    """

    rfp_id: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)


class BaseAgentResult(BaseModel):
    """
    Standardized output from agents.

    - changes: suggested updates to RFP document / tasks
    - events: loggable events for the `events` collection
    - next_state: optional workflow state hint
    """

    success: bool = True
    message: Optional[str] = None

    changes: Dict[str, Any] = Field(default_factory=dict)
    events: Dict[str, Any] = Field(default_factory=dict)
    next_state: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all RFP Studio agents.

    Concrete agents should implement:
        async def run(self, agent_input: BaseAgentInput) -> BaseAgentResult
    """

    def __init__(self, config: BaseAgentConfig):
        self.config = config

    @abstractmethod
    async def run(self, agent_input: BaseAgentInput) -> BaseAgentResult:
        """
        Execute the agent's core logic.

        This method should:
        - Read the RFP / tasks / KB as needed
        - Use LLMs / vector search if applicable
        - Return a BaseAgentResult with changes + events
        """
        raise NotImplementedError("Agents must implement the run() method.")
