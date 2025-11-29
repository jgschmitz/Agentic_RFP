# rfp_studio/agents/legal.py

"""
Legal Agent for RFP Studio.

Responsibilities:
- Review draft RFP content for legal compliance
- Identify and flag potential legal risks
- Suggest contract terms and liability limitations
- Ensure regulatory compliance
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


class LegalAgent(BaseAgent):
    """
    Agent that reviews RFP content for legal compliance.

    Expected payload schema:
        {
            "tasks": [
                {
                    "task_id": "ObjectId string",
                    "review_type": "contract_terms" | "liability" | "compliance" | "general",
                    "content": "Content to review...",
                    "client_jurisdiction": "US" | "EU" | "CA",
                    "industry_regulations": ["HIPAA", "SOX", "GDPR"]
                }
            ]
        }
    """

    def __init__(self, config: Optional[BaseAgentConfig] = None):
        super().__init__(
            config
            or BaseAgentConfig(
                name="Legal Agent",
                description="Reviews RFP content for legal compliance and risk assessment.",
                agent_type="LEGAL_AGENT",
            )
        )

    async def run(self, agent_input: BaseAgentInput) -> BaseAgentResult:
        db = get_db()
        payload = agent_input.payload or {}
        rfp_id = agent_input.rfp_id

        tasks_to_review = payload.get("tasks", [])
        if not tasks_to_review:
            return BaseAgentResult(
                success=False,
                message="LegalAgent requires 'tasks' in payload.",
            )

        reviewed_task_ids: List[str] = []
        review_results: List[Dict[str, Any]] = []
        now_iso = datetime.utcnow().isoformat()

        for task_info in tasks_to_review:
            task_id = task_info.get("task_id")
            if not task_id:
                continue

            try:
                task_oid = ObjectId(task_id)
            except Exception:
                continue

            # Perform legal review (stub implementation)
            review_result = self._perform_legal_review(task_info)

            # Update task with review
            task_collection = db["tasks"]
            update_result = task_collection.update_one(
                {"_id": task_oid},
                {
                    "$set": {
                        "status": TaskStatus.COMPLETED.value,
                        "updated_at": now_iso,
                        "metadata.legal_review": review_result,
                        "metadata.legal_agent": {
                            "source_agent": self.config.agent_type,
                            "timestamp": now_iso,
                            "review_type": task_info.get("review_type"),
                        },
                    }
                },
            )

            if update_result.matched_count:
                reviewed_task_ids.append(task_id)
                review_results.append({
                    "task_id": task_id,
                    "review_type": task_info.get("review_type"),
                    "risk_level": review_result.get("risk_level"),
                    "issues_found": len(review_result.get("issues", [])),
                    "status": "reviewed",
                })

        # Suggest next workflow state
        next_state = None
        if can_transition(RFPStatus.LEGAL_REVIEW, RFPStatus.QUALITY_REVIEW):
            next_state = RFPStatus.QUALITY_REVIEW.value

        event = {
            "type": "LEGAL_REVIEW_COMPLETED",
            "rfp_id": rfp_id,
            "source_agent": self.config.agent_type,
            "timestamp": now_iso,
            "payload": {
                "num_tasks": len(tasks_to_review),
                "num_reviewed": len(reviewed_task_ids),
                "review_results": review_results,
            },
        }

        return BaseAgentResult(
            success=True,
            message=f"LegalAgent reviewed {len(reviewed_task_ids)} sections.",
            changes={"reviewed_task_ids": reviewed_task_ids},
            events={"legal_review_completed": event},
            next_state=next_state,
        )

    def _perform_legal_review(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform legal review of content (stub implementation).
        
        In a full implementation, this would:
        - Use legal AI models to analyze content
        - Check against regulatory databases
        - Apply jurisdiction-specific rules
        - Generate detailed compliance reports
        """
        review_type = task_info.get("review_type", "general")
        content = task_info.get("content", "")
        jurisdiction = task_info.get("client_jurisdiction", "US")
        regulations = task_info.get("industry_regulations", [])

        # Stub implementation - would use legal AI/knowledge base in production
        review_templates = {
            "contract_terms": {
                "risk_level": "medium",
                "summary": "Contract terms reviewed for standard compliance",
                "issues": [
                    "Consider adding liability limitation clause",
                    "Recommend specifying data retention period",
                    "Review termination clause language"
                ],
                "recommendations": [
                    "Add 'limitation of liability to fees paid' clause",
                    "Specify 30-day data deletion upon termination",
                    "Include 30-day notice period for termination"
                ]
            },
            
            "liability": {
                "risk_level": "high",
                "summary": "Liability exposure analysis completed",
                "issues": [
                    "Unlimited liability exposure identified",
                    "No force majeure clause present"
                ],
                "recommendations": [
                    "Cap liability at 12 months of fees",
                    "Add standard force majeure provisions",
                    "Include indemnification mutual terms"
                ]
            },
            
            "compliance": {
                "risk_level": "low",
                "summary": f"Compliance review for {', '.join(regulations)} regulations",
                "issues": [
                    f"Verify {regulation} compliance documentation" for regulation in regulations[:2]
                ],
                "recommendations": [
                    "Maintain current compliance documentation",
                    "Regular compliance audits recommended"
                ]
            }
        }

        base_review = review_templates.get(review_type, {
            "risk_level": "low",
            "summary": "General legal review completed",
            "issues": [],
            "recommendations": ["Standard legal review - no issues identified"]
        })

        # Add jurisdiction-specific notes
        if jurisdiction == "EU":
            base_review["notes"] = ["GDPR compliance verified", "EU contract law applicable"]
        elif jurisdiction == "CA":
            base_review["notes"] = ["Canadian privacy laws considered", "Provincial regulations reviewed"]
        else:
            base_review["notes"] = ["US federal and state laws considered"]

        return base_review