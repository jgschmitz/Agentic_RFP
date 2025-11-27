# rfp_studio/agents/sme_router.py

"""
SME Routing Agent for RFP Studio.

Responsibilities:
- Take questions / sections (usually from BDM-created tasks)
- Embed them using OpenAI embeddings
- Use MongoDB Atlas Vector Search to find the best SME / team
- Update tasks with assigned SME teams
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from bson import ObjectId

from openai import OpenAI

from rfp_studio.agents.base import (
    BaseAgent,
    BaseAgentConfig,
    BaseAgentInput,
    BaseAgentResult,
)
from rfp_studio.config import get_settings
from rfp_studio.db.atlas import get_db
from rfp_studio.models.task import TaskStatus


class SMERoutingAgent(BaseAgent):
    """
    Agent that routes questions to SME teams using Atlas Vector Search.

    Assumptions:
    - There is a `knowledge_base` collection in MongoDB Atlas.
    - Each KB document has:
        - `embedding`: list[float]
        - `team_key`: str (e.g. "sme_team_security", "sme_team_compliance")
      and optionally:
        - `tags`, `topic`, etc. for future filtering.

    Expected payload structure:

        {
            "questions": [
                {"task_id": "<task ObjectId as string>", "text": "..." },
                ...
            ]
        }

    The agent will:
    - Compute an embedding for each `text`
    - Run a vector search against `knowledge_base`
    - Choose the top match's `team_key`
    - Update the corresponding task's `assigned_to_team` and metadata
    """

    def __init__(self, config: Optional[BaseAgentConfig] = None):
        super().__init__(
            config
            or BaseAgentConfig(
                name="SME Routing Agent",
                description="Routes RFP questions to SME teams using Atlas Vector Search.",
                agent_type="SME_ROUTING_AGENT",
            )
        )
        settings = get_settings()
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set for SMERoutingAgent.")
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._kb_index = settings.atlas_vector_index_kb

    async def run(self, agent_input: BaseAgentInput) -> BaseAgentResult:
        db = get_db()
        settings = get_settings()

        payload = agent_input.payload or {}
        questions: List[Dict[str, Any]] = payload.get("questions") or []

        if not questions:
            return BaseAgentResult(
                success=False,
                message="SMERoutingAgent payload missing 'questions'.",
            )

        updated_tasks: List[str] = []
        routing_details: List[Dict[str, Any]] = []
        now_iso = datetime.utcnow().isoformat()

        for q in questions:
            task_id = q.get("task_id")
            text = (q.get("text") or "").strip()

            if not task_id or not text:
                # Skip invalid entries but don't fail whole agent
                continue

            try:
                embedding = self._embed_text(text)
            except Exception as e:
                # If embedding fails, skip this question but continue others
                routing_details.append(
                    {
                        "task_id": task_id,
                        "status": "embedding_failed",
                        "error": str(e),
                    }
                )
                continue

            # ----- Vector Search against Atlas -----
            kb_collection = db["knowledge_base"]

            pipeline = [
                {
                    "$vectorSearch": {
                        "index": self._kb_index,
                        "queryVector": embedding,
                        "path": "embedding",
                        "numCandidates": 200,
                        "limit": 3,
                    }
                },
                {
                    "$project": {
                        "_id": 1,
                        "team_key": 1,
                        "topic": 1,
                        "score": {"$meta": "vectorSearchScore"},
                    }
                },
                {"$limit": 3},
            ]

            results = list(kb_collection.aggregate(pipeline))
            if not results:
                routing_details.append(
                    {
                        "task_id": task_id,
                        "status": "no_match",
                    }
                )
                continue

            top_match = results[0]
            team_key = (
                top_match.get("team_key")
                or top_match.get("team")
                or top_match.get("owner_team")
            )

            if not team_key:
                routing_details.append(
                    {
                        "task_id": task_id,
                        "status": "no_team_in_match",
                    }
                )
                continue

            # ----- Update the task with assigned SME team -----
            try:
                task_oid = ObjectId(task_id)
            except Exception:
                routing_details.append(
                    {
                        "task_id": task_id,
                        "status": "invalid_task_id",
                    }
                )
                continue

            task_collection = db["tasks"]
            update_result = task_collection.update_one(
                {"_id": task_oid},
                {
                    "$set": {
                        "assigned_to_team": team_key,
                        "status": TaskStatus.PENDING.value,
                        "updated_at": now_iso,
                        "metadata.sme_routing": {
                            "source_agent": self.config.agent_type,
                            "matched_kb_id": str(top_match.get("_id")),
                            "score": top_match.get("score"),
                            "timestamp": now_iso,
                        },
                    }
                },
            )

            if update_result.matched_count:
                updated_tasks.append(task_id)
                routing_details.append(
                    {
                        "task_id": task_id,
                        "status": "routed",
                        "assigned_to_team": team_key,
                        "kb_match_id": str(top_match.get("_id")),
                        "score": top_match.get("score"),
                    }
                )
            else:
                routing_details.append(
                    {
                        "task_id": task_id,
                        "status": "task_not_found",
                    }
                )

        event = {
            "type": "SME_ROUTING_COMPLETED",
            "source_agent": self.config.agent_type,
            "timestamp": now_iso,
            "payload": {
                "num_questions": len(questions),
                "num_routed": len(updated_tasks),
                "details": routing_details,
            },
        }

        return BaseAgentResult(
            success=True,
            message=f"SMERoutingAgent processed {len(questions)} questions.",
            changes={"updated_task_ids": updated_tasks},
            events={"sme_routing_completed": event},
            next_state=None,  # routing doesn't necessarily advance workflow
        )

    # ---------- Internal helpers ----------

    def _embed_text(self, text: str) -> List[float]:
        """
        Generate an embedding for the given text using OpenAI.

        Uses 'text-embedding-3-small' by default for cost efficiency.
        """
        response = self._client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        return response.data[0].embedding
