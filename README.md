# 📄 RFP Studio --- Agentic RFP Automation Platform

> **AI‑orchestrated RFP automation powered by Python, LangGraph, and
> MongoDB Atlas Vector Search.** From intake → SME routing → drafting →
> legal → final submission --- fully automated.

------------------------------------------------------------------------

## 🚀 1. Overview

**RFP Studio** is an AI-driven, agent-orchestrated workflow engine that
automates the entire **RFP lifecycle**.

🧩 **Core Idea:**\
Each RFP is stored as a structured MongoDB document. Agents read/write
updates as the workflow progresses.

Lifecycle: **Intake → Breakdown → SME Routing → Draft → Legal → Quality
→ VP Approval → Submission**

------------------------------------------------------------------------

## 🏗️ 2. Architecture Diagram (Text)

    Frontend (Web UI / CLI)
            ↓
    API Gateway (FastAPI)
            ↓
    Agent Orchestrator (LangGraph)
            ↓
    MongoDB Atlas (Docs + Vectors + Triggers)
            ↓
    Atlas Vector Search (SME routing + Answer reuse + Similarity)

------------------------------------------------------------------------

## 🧠 3. Core Concepts

-   📘 **Structured RFP Objects** --- RFPs stored as MongoDB documents\
-   🤖 **Agents** --- Sales, BDM, SME Router, Writer, Legal, Quality,
    Submission\
-   🔄 **State Machine** --- Drives all workflow transitions\
-   🔍 **Vector Search** --- Reuse answers, detect conflicts, route
    SMEs\
-   ⚡ **MongoDB Triggers** --- Keep history, events, lifecycle clean

------------------------------------------------------------------------

## 🗄️ 4. MongoDB RFP Schema (High-Level)

``` json
{
  "_id": "RFP12345",
  "title": "...",
  "client": {"name": "", "contact": ""},
  "status": "INITIATED",
  "timeline": {"received_date": "", "due_date": "", "milestones": []},
  "participants": {
    "sales_team": [],
    "bdm": "",
    "writers": [],
    "smes": []
  },
  "tasks": [],
  "documents": {
    "original_rfp_url": "",
    "draft_document_url": "",
    "final_document_url": ""
  },
  "history": [],
  "metadata": {"industry": "", "rfp_size": "", "tags": []}
}
```

------------------------------------------------------------------------

## 🔁 5. Workflow State Machine

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

------------------------------------------------------------------------

## 🧩 6. Recommended Agent Types

-   **Sales Agent** --- Extracts opportunity details, initializes RFP\
-   **BDM Agent** --- Reads full RFP, breaks down sections, assigns
    SMEs\
-   **SME Routing Agent** --- Uses vector search to match SMEs\
-   **SME Answer Agent** --- Drafts or retrieves similar answers\
-   **Writer Agent** --- Builds the Draft RFP\
-   **Legal Agent** --- Flags risk, compliance, contracting issues\
-   **Quality Agent** --- Tone, formatting, consistency\
-   **VP Approval Agent** --- Summaries + approval readiness\
-   **Submission Agent** --- Final packaging + export

------------------------------------------------------------------------

## 🗂️ 7. MongoDB Collections

-   `rfps`
-   `tasks`
-   `users`
-   `knowledge_base`
-   `events`

------------------------------------------------------------------------

## 🧮 8. Vector Search Use Cases

-   🔍 Reuse historical RFP answers\
-   🎯 SME routing\
-   ⚠️ Conflict detection\
-   📝 Writer drafting assistance\
-   📚 Similar RFP recall

------------------------------------------------------------------------

## 🧱 9. Build Plan

**Phase 1:** MongoDB + Schema + API\
**Phase 2:** Agents (Sales → BDM → SME → Writer → Legal → Quality)\
**Phase 3:** Workflow Engine (State Machine)\
**Phase 4:** Draft Pipeline + Knowledge Base\
**Phase 5:** Submission + Export Tools

------------------------------------------------------------------------

## 🌟 10. Core Principles

-   RFPs stored as structured objects\
-   Agents operate on clean fields\
-   Workflow automation is state-driven\
-   Vector search powers reuse\
-   MongoDB Atlas = single source of truth

------------------------------------------------------------------------

## 📊 11. Summary Table

  Category         Details
  ---------------- -------------------------------------------------
  **Goal**         Build an agentic RFP workflow platform
  **Tech Stack**   Python, MongoDB Atlas, Vector Search, LangGraph
  **Agents**       Sales, BDM, SME, Writer, Legal, QA, Submission
  **Benefits**     Speed, consistency, reduced manual work

------------------------------------------------------------------------

## 🧪 12. Getting Started

    git clone https://github.com/your-org/rfp-studio
    cd rfp-studio
    pip install -r requirements.txt
    python app.py

------------------------------------------------------------------------

## 📜 License

MIT (or your preferred license)

------------------------------------------------------------------------

## 🤝 Contributing

PRs welcome!
