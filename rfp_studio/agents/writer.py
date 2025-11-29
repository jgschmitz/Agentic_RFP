# rfp_studio/agents/writer.py

"""
Writer Agent for RFP Studio.

Responsibilities:
- Generate draft content for RFP sections
- Use templates and prior RFP content for consistency
- Coordinate with SME answers to create comprehensive responses
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

from rfp_studio.agents.base import (
    BaseAgent,
    BaseAgentConfig,
    BaseAgentInput,
    BaseAgentResult,
)
from rfp_studio.db.atlas import get_db
from rfp_studio.models.task import TaskStatus
from rfp_studio.workflow.states import RFPStatus, can_transition


class WriterAgent(BaseAgent):
    """
    Agent that generates draft content for RFP responses.

    Expected payload schema:
        {
            "tasks": [
                {
                    "task_id": "ObjectId string",
                    "content_type": "executive_summary" | "technical_response" | "pricing",
                    "template_style": "formal" | "conversational",
                    "requirements": "Specific requirements for this section...",
                    "sme_inputs": ["Answer from security team...", "..."]
                }
            ]
        }
    """

    def __init__(self, config: Optional[BaseAgentConfig] = None):
        super().__init__(
            config
            or BaseAgentConfig(
                name="Writer Agent",
                description="Generates draft content for RFP sections using templates and SME inputs.",
                agent_type="WRITER_AGENT",
            )
        )

    async def run(self, agent_input: BaseAgentInput) -> BaseAgentResult:
        db = get_db()
        payload = agent_input.payload or {}
        rfp_id = agent_input.rfp_id

        tasks_to_draft = payload.get("tasks", [])
        if not tasks_to_draft:
            return BaseAgentResult(
                success=False,
                message="WriterAgent requires 'tasks' in payload.",
            )

        drafted_task_ids: List[str] = []
        draft_results: List[Dict[str, Any]] = []
        now_iso = datetime.utcnow().isoformat()

        for task_info in tasks_to_draft:
            task_id = task_info.get("task_id")
            if not task_id:
                continue

            try:
                task_oid = ObjectId(task_id)
            except Exception:
                continue

            # Generate draft content (stub implementation)
            draft_content = self._generate_draft_content(task_info)

            # Update task with draft
            task_collection = db["tasks"]
            update_result = task_collection.update_one(
                {"_id": task_oid},
                {
                    "$set": {
                        "status": TaskStatus.COMPLETED.value,
                        "updated_at": now_iso,
                        "metadata.draft_content": draft_content,
                        "metadata.writer_agent": {
                            "source_agent": self.config.agent_type,
                            "timestamp": now_iso,
                            "content_type": task_info.get("content_type"),
                        },
                    }
                },
            )

            if update_result.matched_count:
                drafted_task_ids.append(task_id)
                draft_results.append({
                    "task_id": task_id,
                    "content_type": task_info.get("content_type"),
                    "status": "drafted",
                    "word_count": len(draft_content.split()),
                })

        # Suggest next workflow state
        next_state = None
        if can_transition(RFPStatus.CONTENT_DRAFT, RFPStatus.LEGAL_REVIEW):
            next_state = RFPStatus.LEGAL_REVIEW.value

        event = {
            "type": "CONTENT_DRAFTED",
            "rfp_id": rfp_id,
            "source_agent": self.config.agent_type,
            "timestamp": now_iso,
            "payload": {
                "num_tasks": len(tasks_to_draft),
                "num_drafted": len(drafted_task_ids),
                "draft_results": draft_results,
            },
        }

        return BaseAgentResult(
            success=True,
            message=f"WriterAgent drafted {len(drafted_task_ids)} sections.",
            changes={"drafted_task_ids": drafted_task_ids},
            events={"content_drafted": event},
            next_state=next_state,
        )

    def _generate_draft_content(self, task_info: Dict[str, Any]) -> str:
        """
        Generate draft content for a task (stub implementation).
        
        In a full implementation, this would:
        - Use LLM to generate content based on requirements
        - Apply templates based on content_type
        - Incorporate SME inputs appropriately
        """
        content_type = task_info.get("content_type", "general")
        requirements = task_info.get("requirements", "")
        sme_inputs = task_info.get("sme_inputs", [])

        # Stub implementation - would use LLM in production
        draft_templates = {
            "executive_summary": f"""
## Executive Summary

Based on the requirements: {requirements}

Our organization is well-positioned to deliver comprehensive solutions that meet your specified needs. 
With our proven track record and expert team, we provide:

{self._format_sme_inputs(sme_inputs)}

We are committed to delivering exceptional value and look forward to partnering with you.
            """.strip(),
            
            "technical_response": f"""
## Technical Response

### Requirements Analysis
{requirements}

### Our Approach
{self._format_sme_inputs(sme_inputs)}

### Implementation Plan
1. Assessment and planning phase
2. Solution design and architecture
3. Implementation and testing
4. Deployment and support

### Technical Specifications
[Detailed specifications would be provided here based on SME input]
            """.strip(),
            
            "pricing": f"""
## Pricing and Commercial Terms

### Investment Overview
Based on your requirements: {requirements}

### Pricing Structure
- Setup and implementation costs
- Ongoing subscription/licensing fees  
- Optional professional services

{self._format_sme_inputs(sme_inputs)}

### Value Proposition
Our pricing reflects the comprehensive value delivered through our solution.
            """.strip(),
        }

        return draft_templates.get(content_type, f"""
## Response

Requirements: {requirements}

{self._format_sme_inputs(sme_inputs)}

[This section would be expanded with detailed content based on the specific requirements.]
        """.strip())

    def _format_sme_inputs(self, sme_inputs: List[str]) -> str:
        """Format SME inputs into readable content."""
        if not sme_inputs:
            return "• Comprehensive expertise across all relevant domains"
        
        formatted = []
        for i, sme_input in enumerate(sme_inputs, 1):
            formatted.append(f"• {sme_input}")
        
        return "\n".join(formatted)