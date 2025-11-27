# rfp_studio/agents/sales.py

"""
Sales Agent for RFP Studio.

Responsibilities:
- Create or enrich an RFP document at the very start of the lifecycle
- Normalize sales-provided details into the structured RFP schema
- Optionally advance workflow from INITIATED → LINKED_TO_RFP
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from bson import ObjectId

from rfp_studio.agents.base import (
    BaseAgent,
    BaseAgentConfig,
    BaseAgentInput,
    BaseAgentResult,
)
from rfp_studio.db.atlas import get_db
from rfp_studio.models.rfp import RFP, serialize_mongo_doc
from rfp_studio.workflow.states import RFPStatus, can_transition


class SalesAgent(BaseAgent):
    """
    Agent that handles initial RFP intake from Sales.

    Expected payload fields (flexible, but typically):
    - title: str
    - client_name: str
    - client_contact: Optional[str]
    - received_date: Optional[str]
    - due_date: Optional[str]
    - metadata: Optional[dict]
    """

    def __init__(self, config: Optional[BaseAgentConfig] = None):
        super().__init__(
            config
            or BaseAgentConfig(
                name="Sales Agent",
                description="Handles intake and creation of structured RFP records.",
                agent_type="SALES_AGENT",
            )
        )

    async def run(self, agent_input: BaseAgentInput) -> BaseAgentResult:
        db = get_db()
        payload = agent_input.payload or {}

        rfp_id = agent_input.rfp_id
        is_new = rfp_id is None

        if is_new:
            # ----- Create a new RFP document -----
            try:
                rfp_model = self._build_new_rfp_model(payload)
            except ValueError as e:
                return BaseAgentResult(
                    success=False,
                    message=f"SalesAgent failed to construct RFP: {e}",
                )

            rfp_dict = rfp_model.model_dump()
            rfp_dict["created_at"] = datetime.utcnow().isoformat()

            result = db.rfps.insert_one(rfp_dict)
            new_id = str(result.inserted_id)

            stored = db.rfps.find_one({"_id": ObjectId(new_id)})
            serialized = serialize_mongo_doc(stored)

            event = {
                "type": "RFP_CREATED",
                "rfp_id": new_id,
                "source_agent": self.config.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": {
                    "title": rfp_model.title,
                    "client_name": rfp_model.client.name,
                },
            }

            # Optionally suggest moving INITIATED → LINKED_TO_RFP
            next_state = None
            if can_transition(RFPStatus.INITIATED, RFPStatus.LINKED_TO_RFP):
                next_state = RFPStatus.LINKED_TO_RFP.value

            return BaseAgentResult(
                success=True,
                message="RFP created by SalesAgent.",
                changes={"rfp": serialized},
                events={"rfp_created": event},
                next_state=next_state,
            )

        else:
            # ----- Enrich an existing RFP -----
            try:
                oid = ObjectId(rfp_id)
            except Exception:
                return BaseAgentResult(
                    success=False,
                    message=f"Invalid rfp_id provided to SalesAgent: {rfp_id}",
                )

            existing = db.rfps.find_one({"_id": oid})
            if not existing:
                return BaseAgentResult(
                    success=False,
                    message=f"No RFP found with id={rfp_id}",
                )

            # Merge incoming payload into existing doc at well-known places
            updates: Dict[str, Any] = {}
            metadata_updates = payload.get("metadata") or {}
            if metadata_updates:
                updates["metadata"] = {**existing.get("metadata", {}), **metadata_updates}

            client_name = payload.get("client_name")
            client_contact = payload.get("client_contact")
            if client_name or client_contact:
                existing_client = existing.get("client", {}) or {}
                updates["client"] = {
                    **existing_client,
                    **(
                        {"name": client_name}
                        if client_name is not None
                        else {}
                    ),
                    **(
                        {"contact": client_contact}
                        if client_contact is not None
                        else {}
                    ),
                }

            title = payload.get("title")
            if title:
                updates["title"] = title

            # Timeline hints
            received_date = payload.get("received_date")
            due_date = payload.get("due_date")
            if received_date or due_date:
                existing_timeline = existing.get("timeline", {}) or {}
                updates["timeline"] = {
                    **existing_timeline,
                    **(
                        {"received_date": received_date}
                        if received_date is not None
                        else {}
                    ),
                    **(
                        {"due_date": due_date}
                        if due_date is not None
                        else {}
                    ),
                }

            if not updates:
                return BaseAgentResult(
                    success=True,
                    message="SalesAgent had no updates to apply.",
                    changes={},
                    events={},
                    next_state=None,
                )

            updates["updated_at"] = datetime.utcnow().isoformat()

            db.rfps.update_one({"_id": oid}, {"$set": updates})
            refreshed = db.rfps.find_one({"_id": oid})
            serialized = serialize_mongo_doc(refreshed)

            event = {
                "type": "RFP_UPDATED_BY_SALES",
                "rfp_id": rfp_id,
                "source_agent": self.config.agent_type,
                "timestamp": datetime.utcnow().isoformat(),
                "payload": payload,
            }

            return BaseAgentResult(
                success=True,
                message="RFP updated by SalesAgent.",
                changes={"rfp": serialized},
                events={"rfp_updated_by_sales": event},
                next_state=None,
            )

    # ---------- Internal helpers ----------

    def _build_new_rfp_model(self, payload: dict) -> RFP:
        """
        Build a new RFP model from raw payload.

        Minimal required:
        - title
        - client_name
        """
        title = payload.get("title")
        client_name = payload.get("client_name")
        client_contact = payload.get("client_contact")

        if not title:
            raise ValueError("Missing 'title' in SalesAgent payload")
        if not client_name:
            raise ValueError("Missing 'client_name' in SalesAgent payload")

        received_date = payload.get("received_date")
        due_date = payload.get("due_date")

        from rfp_studio.models.rfp import ClientInfo, Timeline, Participants, DocumentLinks, Metadata

        return RFP(
            title=title,
            client=ClientInfo(name=client_name, contact=client_contact),
            status="INITIATED",
            timeline=Timeline(
                received_date=received_date,
                due_date=due_date,
            ),
            participants=Participants(),
            documents=DocumentLinks(),
            metadata=Metadata(
                industry=payload.get("industry"),
                rfp_size=payload.get("rfp_size"),
                tags=payload.get("tags") or [],
            ),
        )
