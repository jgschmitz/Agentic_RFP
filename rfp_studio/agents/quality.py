# rfp_studio/agents/quality.py

"""
Quality Agent for RFP Studio.

Responsibilities:
- Review final RFP content for quality and consistency
- Check formatting, grammar, and professional presentation
- Ensure all requirements are addressed
- Validate completeness before final approval
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


class QualityAgent(BaseAgent):
    """
    Agent that performs final quality assurance on RFP content.

    Expected payload schema:
        {
            "tasks": [
                {
                    "task_id": "ObjectId string",
                    "content": "Final content to review...",
                    "requirements_checklist": ["Requirement 1", "Requirement 2"],
                    "quality_criteria": {
                        "check_grammar": true,
                        "check_formatting": true,
                        "check_completeness": true,
                        "check_consistency": true
                    }
                }
            ]
        }
    """

    def __init__(self, config: Optional[BaseAgentConfig] = None):
        super().__init__(
            config
            or BaseAgentConfig(
                name="Quality Agent",
                description="Performs final quality assurance and completeness checks on RFP content.",
                agent_type="QUALITY_AGENT",
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
                message="QualityAgent requires 'tasks' in payload.",
            )

        reviewed_task_ids: List[str] = []
        quality_results: List[Dict[str, Any]] = []
        overall_quality_score = 0.0
        now_iso = datetime.utcnow().isoformat()

        for task_info in tasks_to_review:
            task_id = task_info.get("task_id")
            if not task_id:
                continue

            try:
                task_oid = ObjectId(task_id)
            except Exception:
                continue

            # Perform quality review (stub implementation)
            quality_result = self._perform_quality_review(task_info)
            overall_quality_score += quality_result.get("quality_score", 0.0)

            # Update task with quality review
            task_collection = db["tasks"]
            update_result = task_collection.update_one(
                {"_id": task_oid},
                {
                    "$set": {
                        "status": TaskStatus.COMPLETED.value,
                        "updated_at": now_iso,
                        "metadata.quality_review": quality_result,
                        "metadata.quality_agent": {
                            "source_agent": self.config.agent_type,
                            "timestamp": now_iso,
                            "quality_score": quality_result.get("quality_score"),
                        },
                    }
                },
            )

            if update_result.matched_count:
                reviewed_task_ids.append(task_id)
                quality_results.append({
                    "task_id": task_id,
                    "quality_score": quality_result.get("quality_score"),
                    "issues_found": len(quality_result.get("issues", [])),
                    "requirements_met": quality_result.get("requirements_coverage", 0),
                    "status": "reviewed",
                })

        # Calculate average quality score
        avg_quality_score = (
            overall_quality_score / len(tasks_to_review) if tasks_to_review else 0.0
        )

        # Suggest next workflow state based on quality
        next_state = None
        if avg_quality_score >= 0.85:  # High quality threshold
            if can_transition(RFPStatus.QUALITY_REVIEW, RFPStatus.FINAL_RFP):
                next_state = RFPStatus.FINAL_RFP.value
        # If quality is below threshold, might stay in current state or go back

        event = {
            "type": "QUALITY_REVIEW_COMPLETED",
            "rfp_id": rfp_id,
            "source_agent": self.config.agent_type,
            "timestamp": now_iso,
            "payload": {
                "num_tasks": len(tasks_to_review),
                "num_reviewed": len(reviewed_task_ids),
                "avg_quality_score": avg_quality_score,
                "quality_results": quality_results,
            },
        }

        return BaseAgentResult(
            success=True,
            message=f"QualityAgent reviewed {len(reviewed_task_ids)} sections with avg score {avg_quality_score:.2f}.",
            changes={"reviewed_task_ids": reviewed_task_ids, "quality_score": avg_quality_score},
            events={"quality_review_completed": event},
            next_state=next_state,
        )

    def _perform_quality_review(self, task_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform quality review of content (stub implementation).
        
        In a full implementation, this would:
        - Use NLP models for grammar and style checking
        - Validate formatting against templates
        - Cross-check requirements coverage
        - Generate detailed quality metrics
        """
        content = task_info.get("content", "")
        requirements = task_info.get("requirements_checklist", [])
        quality_criteria = task_info.get("quality_criteria", {})

        # Stub implementation - would use quality AI models in production
        quality_checks = {
            "grammar_score": self._check_grammar(content),
            "formatting_score": self._check_formatting(content),
            "completeness_score": self._check_completeness(content, requirements),
            "consistency_score": self._check_consistency(content),
        }

        # Calculate overall quality score (0.0 to 1.0)
        enabled_checks = [
            score for check, score in quality_checks.items()
            if quality_criteria.get(check.replace("_score", ""), True)
        ]
        quality_score = sum(enabled_checks) / len(enabled_checks) if enabled_checks else 0.8

        # Identify issues based on scores
        issues = []
        recommendations = []

        if quality_checks["grammar_score"] < 0.8:
            issues.append("Grammar and style improvements needed")
            recommendations.append("Run content through professional editing")

        if quality_checks["formatting_score"] < 0.8:
            issues.append("Formatting inconsistencies detected")
            recommendations.append("Apply consistent formatting template")

        if quality_checks["completeness_score"] < 0.9:
            issues.append("Some requirements may not be fully addressed")
            recommendations.append("Review and expand sections missing requirement coverage")

        if quality_checks["consistency_score"] < 0.8:
            issues.append("Inconsistent terminology or messaging")
            recommendations.append("Standardize key terms and messaging across sections")

        return {
            "quality_score": round(quality_score, 2),
            "detailed_scores": quality_checks,
            "requirements_coverage": round(quality_checks["completeness_score"], 2),
            "issues": issues,
            "recommendations": recommendations,
            "word_count": len(content.split()),
            "readability": "Professional" if quality_score > 0.8 else "Needs improvement",
        }

    def _check_grammar(self, content: str) -> float:
        """Stub grammar check - returns score 0.0-1.0"""
        # Simple heuristics - in production would use grammar checking AI
        if len(content) < 50:
            return 0.7
        
        # Check for basic issues
        issues = 0
        if ".." in content:
            issues += 1
        if "  " in content:  # Double spaces
            issues += 1
        if content.count("!") > len(content) / 100:  # Too many exclamations
            issues += 1
            
        return max(0.8 - (issues * 0.1), 0.6)

    def _check_formatting(self, content: str) -> float:
        """Stub formatting check - returns score 0.0-1.0"""
        # Check for consistent formatting patterns
        score = 0.9
        
        if "##" in content and "#" in content:  # Mixed heading styles
            score -= 0.1
        if not any(line.strip().startswith(("•", "-", "1.")) for line in content.split("\n")):
            if len(content) > 200:  # Long content should have lists
                score -= 0.1
                
        return max(score, 0.7)

    def _check_completeness(self, content: str, requirements: List[str]) -> float:
        """Stub completeness check - returns score 0.0-1.0"""
        if not requirements:
            return 0.9  # No requirements to check
            
        # Simple keyword matching - in production would use semantic analysis
        content_lower = content.lower()
        covered = 0
        
        for req in requirements:
            # Very basic keyword presence check
            req_words = req.lower().split()
            if any(word in content_lower for word in req_words if len(word) > 3):
                covered += 1
                
        return covered / len(requirements) if requirements else 1.0

    def _check_consistency(self, content: str) -> float:
        """Stub consistency check - returns score 0.0-1.0"""
        # Check for consistent style and terminology
        lines = content.split("\n")
        if len(lines) < 5:
            return 0.8
            
        # Basic consistency checks
        score = 0.9
        
        # Check heading consistency
        headings = [line for line in lines if line.startswith("#")]
        if len(set(len(h.split("#")[0]) for h in headings)) > 2:
            score -= 0.1  # Inconsistent heading levels
            
        return max(score, 0.7)