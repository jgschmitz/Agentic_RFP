
# 📄 RFP Studio — Agentic RFP Automation Platform

> **AI‑orchestrated RFP automation powered by Python, LangGraph, and MongoDB Atlas Vector Search.**  
End‑to‑end automation: intake → BDM breakdown → SME routing → drafting → legal → quality → submission.

---

## 🚀 1. Overview

**RFP Studio** is an agent-driven workflow system built on **MongoDB Atlas** and **LangGraph**.  
Each agent performs a domain-specific role, and the orchestrator wires them into a deterministic pipeline.

Core capabilities:
- Fully structured **RFP documents** stored in Atlas  
- **Sales → BDM → SME → Writer → Legal → QA** agent network  
- **Atlas Vector Search** for SME routing & answer reuse  
- Clean, framework‑agnostic Python package (no FastAPI required)  
- Modular agents you can run independently or as a flow  

---

## 🏗️ 2. Project Structure

```
rfp_studio/
│
├── agents/
│   ├── base.py
│   ├── sales.py
│   ├── bdm.py
│   ├── sme_router.py
│
├── orchestrator/
│   └── langgraph_flow.py
│
├── vector/
│   ├── embeddings.py
│   └── atlas_query.py
│
├── knowledge/
│   └── loader.py
│
├── models/
│   ├── rfp.py
│   └── task.py
│
├── workflow/
│   └── states.py
│
├── db/
│   └── atlas.py
│
└── config.py
```

---

## 🗄️ 3. MongoDB Atlas Schema (High-Level)

Each RFP is stored as a structured document:

```json
{
  "_id": "ObjectId",
  "title": "...",
  "client": {"name": "", "contact": ""},
  "status": "INITIATED",
  "timeline": {"received_date": "", "due_date": "", "milestones": []},
  "participants": {"sales_team": [], "bdm": "", "writers": [], "smes": []},
  "tasks": [],
  "documents": {
    "original_rfp_url": "",
    "draft_document_url": "",
    "final_document_url": ""
  },
  "history": [],
  "metadata": {"industry": "", "rfp_size": "", "tags": []},
  "embedding": []
}
```

---

## 🔁 4. Workflow State Machine

```
INITIATED
→ LINKED_TO_RFP
→ SALES_ASSEMBLY
→ BDM_REVIEW
→ RFP_BREAKDOWN
→ SME_QA
→ CONTENT_DRAFT
→ LEGAL_REVIEW
→ QUALITY_REVIEW
→ FINAL_RFP
→ APPROVED_BY_VP
→ SUBMISSION_READY
→ SUBMITTED
```

---

## 🤖 5. Agent Layer

### ✔️ Sales Agent (`agents/sales.py`)
Creates or enriches an RFP record.

### ✔️ BDM Review Agent (`agents/bdm.py`)
Breaks the RFP into tasks and work units.

### ✔️ SME Routing Agent (`agents/sme_router.py`)
Uses embeddings + Atlas Vector Search to assign tasks to SME teams.

(Writer, Legal, Quality, Submission coming soon)

---

## 🧠 6. Vector Intelligence

Powered by **embeddings + Atlas Vector Search**:

### `vector/embeddings.py`
- OpenAI embeddings  
- Cached client  
- Single/batch support  

### `vector/atlas_query.py`
- Generic `$vectorSearch` helper  
- `search_knowledge_base()`  
- `search_rfps()`  

---

## 📚 7. Knowledge Base Loader

`knowledge/loader.py` ingests SME knowledge:

- Generates embeddings  
- Attaches SME team keys  
- Stores in `knowledge_base` collection  

---

## 🔀 8. Orchestrator (LangGraph)

`orchestrator/langgraph_flow.py` combines agents into a pipeline:

```
Sales → BDM → SME Routing → END
```

Each agent receives:
- `rfp_id`
- `payload`
- `context`

and returns:
- updates  
- events  
- next workflow state  

---

## 🧪 9. Running a Workflow

Example:

```python
from rfp_studio.orchestrator.langgraph_flow import run_flow

result = await run_flow(
    rfp_id=None,
    payload={
        "title": "RFP for Managed Services",
        "client_name": "Acme Corp",
        "client_contact": "alice@acme.com"
    }
)

print(result)
```

---

## ⚙️ 10. Requirements

```
pymongo[srv]
langgraph
langchain
langchain-openai
openai
pydantic
python-dotenv
requests
tenacity
typer
```

---

## 🛠️ 11. Environment Variables

```
MONGODB_URI=mongodb+srv://...
MONGODB_DB_NAME=rfp_studio
OPENAI_API_KEY=sk-...
ATLAS_VECTOR_INDEX_RFPS=rfp_vector_index
ATLAS_VECTOR_INDEX_KB=kb_vector_index
```

---

## 🤝 12. Contributing

PRs welcome!  
Future roadmap:
- Writer agent  
- Legal agent  
- Quality agent  
- Export + delivery pipeline  
- Full Typer CLI  

---

## 📜 13. License

MIT
