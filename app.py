# app.py
import os
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# ---------- Config ----------

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "rfp_studio")

# ---------- FastAPI App ----------

app = FastAPI(
    title="RFP Studio API",
    version="0.1.0",
    description="Agentic RFP workflow API powered by MongoDB Atlas + Vector Search.",
)

# ---------- MongoDB Client (async) ----------

mongo_client: AsyncIOMotorClient | None = None


@app.on_event("startup")
async def startup_event() -> None:
    global mongo_client
    mongo_client = AsyncIOMotorClient(MONGODB_URI)
    # optional: warm up connection
    await mongo_client.server_info()


@app.on_event("shutdown")
async def shutdown_event() -> None:
    global mongo_client
    if mongo_client is not None:
        mongo_client.close()


def get_db():
    if mongo_client is None:
        raise RuntimeError("Mongo client is not initialized")
    return mongo_client[MONGODB_DB_NAME]


# ---------- Models ----------


class ClientInfo(BaseModel):
    name: str
    contact: Optional[str] = None


class Timeline(BaseModel):
    received_date: Optional[str] = None
    due_date: Optional[str] = None
    milestones: list[dict] = Field(default_factory=list)


class Participants(BaseModel):
    sales_team: list[str] = Field(default_factory=list)
    bdm: Optional[str] = None
    writers: list[str] = Field(default_factory=list)
    smes: list[str] = Field(default_factory=list)


class DocumentsInfo(BaseModel):
    original_rfp_url: Optional[str] = None
    draft_document_url: Optional[str] = None
    final_document_url: Optional[str] = None


class Metadata(BaseModel):
    industry: Optional[str] = None
    rfp_size: Optional[str] = None
    tags: list[str] = Field(default_factory=list)


class RFPCreate(BaseModel):
    title: str
    client: ClientInfo
    status: str = "INITIATED"
    timeline: Timeline = Timeline()
    participants: Participants = Participants()
    tasks: list[dict] = Field(default_factory=list)
    documents: DocumentsInfo = DocumentsInfo()
    history: list[dict] = Field(default_factory=list)
    metadata: Metadata = Metadata()


class RFPOut(RFPCreate):
    id: str = Field(alias="id")


# ---------- Helpers ----------


def serialize_rfp(doc: dict) -> dict:
    """Convert MongoDB document into API-friendly dict."""
    doc = doc.copy()
    doc["id"] = str(doc.pop("_id"))
    return doc


# ---------- Routes ----------


@app.get("/health", tags=["system"])
async def health_check():
    db = get_db()
    # Quick ping to ensure DB connectivity
    await db.command("ping")
    return {"status": "ok"}


@app.post("/rfps", response_model=RFPOut, tags=["rfps"])
async def create_rfp(rfp: RFPCreate):
    db = get_db()
    result = await db.rfps.insert_one(rfp.model_dump())
    stored = await db.rfps.find_one({"_id": result.inserted_id})
    return serialize_rfp(stored)


@app.get("/rfps/{rfp_id}", response_model=RFPOut, tags=["rfps"])
async def get_rfp(rfp_id: str):
    db = get_db()
    try:
        oid = ObjectId(rfp_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid RFP ID")

    doc = await db.rfps.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="RFP not found")
    return serialize_rfp(doc)
