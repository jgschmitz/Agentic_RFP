# rfp_studio/agents/bdm.py

"""
BDM Agent for RFP Studio.

Responsibilities:
- Review an existing RFP
- Break it into sections / work items
- Create tasks for SME Q&A, writer work, etc.
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
from rfp_studio.models.task import Task, TaskType, TaskStatus
from rfp_studio.workflow.states import RFPStatus, can_transition


class BDMReviewAgent(BaseAgent):
    """
    Agent that breaks down an RFP into structured tasks.

    Expected payload schema (example):

        {
            "sections": [
                {
                    "title": "Executive Overview",
                    "description": "...raw text or notes...",
                    "suggested_team": "sales_team",
                    "task_type": "CONTENT_DRAFT"
                },
                {
                    "title": "Security Questionnaire",
                    "description": "...",
                    "suggested_team": "sme_team_security",
                    "task_type": "SME_QA"
                }
            ]
        }
    """

    def __init__(self, config: Optional[BaseAgentConfig] = None):
        super().__init__(
            config
            or BaseAgentConfig(
                name="BDM Review Agent",
                description="Breaks RFP into sections and creates SME / writer tasks.",
                agent_type="BDM_AGENT",
            )
        )

    async def run(self, agent_input: BaseAgentInput) -> BaseAgentResult:
        db = get_db()
        rfp_id = agent_input.rfp_id
        payload = agent_input.payload or {}

        if not rfp_id:
            return BaseAgentResult(
                success=False,
                message="BDMReviewAgent requires rfp_id.",
            )

        try:
            oid = ObjectId(rfp_id)
        except Exception:
            return BaseAgentResult(
                success=False,
                message=f"Invalid rfp_id for BDMReviewAgent: {rfp_id}",
            )

        rfp_doc = db.rfps.find_one({"_id": oid})
        if not rfp_doc:
            return BaseAgentResult(
                success=False,
                message=f"RFP not found for BDMReviewAgent: {rfp_id}",
            )

        sections: List[Dict[str, Any]] = payload.get("sections") or []
        if not sections:
            return BaseAgentResult(
                success=False,
                message="BDMReviewAgent payload missing 'sections'.",
            )

        created_task_ids: List[str] = []
        now_iso = datetime.utcnow().isoformat()

        for section in sections:
            task_type_str = section.get("task_type") or "RFP_BREAKDOWN"
            # Fallback-friendly mapping
            try:
                task_type = TaskType(task_type_str)
            except ValueError:
                task_type = TaskType.RFP_BREAKDOWN

            task_model = Task(
                rfp_id=rfp_id,
                type=task_type,
                status=TaskStatus.PENDING,
                title=section.get("title") or "Untitled section",
                description=section.get("description"),
                assigned_to_team=section.get("suggested_team"),
                metadata={
                    "source": "BDMReviewAgent",
                    "section_index": section.get("index"),
                },
                created_at=now_iso,
                updated_at=now_iso,
            )

            task_dict = task_model.model_dump(exclude_none=True)
            result = db.tasks.insert_one(task_dict)
            created_task_ids.append(str(result.inserted_id))

        # Attach task refs to RFP.tasks for easy navigation
        existing_tasks = rfp_doc.get("tasks") or []
        updated_tasks = existing_tasks + [
            {"task_id": tid, "source": "BDMReviewAgent"} for tid in created_task_ids
        ]

        db.rfps.update_one(
            {"_id": oid},
            {
                "$set": {
                    "tasks": updated_tasks,
                    "updated_at": now_iso,
                }
            },
        )

        # Suggest next workflow state
        next_state = None
        if can_transition(RFPStatus.BDM_REVIEW, RFPStatus.RFP_BREAKDOWN):
            next_state = RFPStatus.RFP_BREAKDOWN.value

        event = {
            "type": "RFP_BREAKDOWN_CREATED",
            "rfp_id": rfp_id,
            "source_agent": self.config.agent_type,
            "timestamp": now_iso,
            "payload": {
                "num_sections": len(sections),
                "task_ids": created_task_ids,
            },
        }

        return BaseAgentResult(
            success=True,
            message=f"BDMReviewAgent created {len(created_task_ids)} tasks.",
            changes={
                "rfp_id": rfp_id,
                "created_task_ids": created_task_ids,
            },
            events={"rfp_breakdown_created": event},
            next_state=next_state,
        )
