# Antigravity AI - Autonomous Marketing Operating System
## Rhythm Academy Organic Growth & CRM Billing Engine

Antigravity AI is an enterprise-grade, tactical marketing operating system designed for **Rhythm Academy** (a music production school). The platform captures top-of-funnel organic social media engagement (Instagram Reels, Facebook Feed, YouTube Shorts), matches intent via trigger keywords, executes automated direct messages, qualifies prospects using **LangGraph state machines**, maps them to relational ledgers, and runs a relentless CRM automated follow-up daemon until they clear split tuition payments.

***

## 1. System Architecture & Intention

The core objective is to create a complete, closed-loop marketing lifecycle that runs automatically:

```
Reel/Short Impression ➔ Comment keyword ("ENROLL") ➔ Webhook Ingestion ➔ Auto-DM 
  ➔ LangGraph State Qualification ➔ WhatsApp Prospect Created ➔ Ad Platform Value Lift 
  ➔ Split Fee Ledger Invoices ➔ Relentless Follow-up Daemon ➔ Tuition Paid ➔ CRM Customer
```

---

## 2. Technology Stack & Core Layers

### 📺 Frontend Dashboard (UI)
*   **Tactical Glassmorphism Theme**: Fully styled with custom CSS `backdrop-blur`, deep glowing radial overlays, responsive grids, neon borders, and hover micro-animations.
*   **Technologies**: HTML5, Tailwind CSS, Space Grotesk/Plus Jakarta Sans typography, and Vanilla Javascript.
*   **Dual Mode Connectivity**: Programmed with AJAX polling (`syncCRMTableData`) targeting the local backend on port `8080`. Automatically drops back to high-fidelity simulated demo states if the server is offline to keep visual telemetry fully active.

### ⚙️ FastAPI Services (Backend)
*   **Server Framework**: **FastAPI** (Python) served by a high-throughput **Uvicorn** ASGI server running on port `8080`.
*   **Security & Webhooks**: Enforces HMAC SHA-256 webhook signature validation to securely authenticate incoming Meta Graph calls and block spoofed payloads instantly with `403 Forbidden` responses.
*   **API Webhooks**: Standardized endpoints for processing XML feeds (YouTube PubSubHubbub), JSON payloads (Meta Webhooks), and custom telemetries.

### 🗄️ SQLite Database Layer (DB)
*   **Storage engine**: SQLite (`backend/antigravity.db`).
*   **Normalized Schemas**:
    *   `CRM_Prospects`: Tracks lead lifecycle stage (Inquiry ➔ Qualified ➔ Customer).
    *   `Platform_Identities`: Maps third-party IDs (WhatsApp numbers, Instagram accounts) to a master profile.
    *   `Rhythm_Academy_Leads`: Stores program registration source and qualification outcomes.
    *   `Rhythm_Installments_Ledger`: Multi-stage tuition split installment records (₹15,000 + ₹15,000) and reminder counts.
    *   `Social_Content_Posts` & `Social_Content_Metrics`: Active creative posts engagement.
    *   `Social_Comment_Captures`: Auditing logs of trigger comments and matched keywords.

---

## 3. LangGraph & LangChain AI Architecture

**Yes, LangGraph and LangChain architectures are actively used.**

Rather than using rigid, hardcoded conditional branches, the conversation funnel and qualification routing are managed by **LangGraph's StateGraph runtime** inside `backend/workflow.py`:

*   **Social Capture Workflow**:
    ```
    social_comment_capture Node ➔ [Keyword Matched?] 
        ➔ YES ➔ auto_dm_dispatcher Node ➔ lead_intent_analyzer Node ➔ END
        ➔ NO ➔ END
    ```
*   **Conversational Nurturing Node**:
    *   `qualify_lead`: Evaluates lead program intent using sentiment scanners.
    *   `dispatch_qualification_message`: Dispatches WhatsApp template structures.
    *   `process_installment_ledger`: Triggers SQLite split tuition ledger generation.
    *   `dispatch_offline_capi_lift`: Interfaces with the `AdAlgorithmOptimizer` to calculate the mathematical value lift of speed-to-lead conversions (base value modulated by response timing multipliers and course boosters) and reports offline feedback signals.

---

## 4. Relentless CRM Follow-Up Engine

The system contains an automated scheduling daemon (`backend/crm_followup_engine.py`) exposed via a POST endpoint `/api/v1/crm/followup` to eliminate leakages in your enrollment funnels:

1.  **Social DM Nudge**: Scans for viewers who left a trigger comment and received the initial DM but didn't respond. Sends a follow-up DM within 2 hours:
    $$\text{"Hey } \{\text{Name}\} \text{! 🎵 Just checking in—did you get a chance to read my previous message..."}$$
2.  **Studio Tour Reminders**: Scans for unqualified inquiries who haven't booked a Studio Tour. Fires a friendly WhatsApp alert prompting them to schedule an analog gear walk-through.
3.  **Split Ledger Reminders**: Scans for active students with unpaid/overdue split installments in their invoices and dispatches WhatsApp billing reminder logs.

---

## 5. Model Context Protocol (MCP) Server Mesh

The agentic capabilities of Antigravity AI are driven by a **Model Context Protocol (MCP) server mesh** configured inside `mcp-servers.json` to allow LLMs to directly read and write to enterprise tools:

| MCP Server | Protocol Scope | Purpose |
|------------|----------------|---------|
| `meta-graph-social` | `@modelcontextprotocol/server-meta-graph` | Triggers Instagram & FB DMs and monitors live comment webhooks. |
| `youtube-data-social`| `@modelcontextprotocol/server-youtube` | Queries channel statistics and registers YouTube video webhooks. |
| `n8n-automation-bridge`| `@modelcontextprotocol/server-n8n` | Orchestrates visual automation flows, triggers nodes, and reads workflow statuses. |
| `postgres-memory` | `@modelcontextprotocol/server-postgres` | Directly reads and writes relational tables inside your PostgreSQL production node. |
| `google-sheets-ledger`| `@modelcontextprotocol/server-google-sheets`| Synchronizes payment records into shared Google Sheets spreadsheets for accounting. |

---

## 6. Directory Map & Codebase

```bash
antigravity-ai/
├── backend/
│   ├── main.py                     # Entrypoint (FastAPI, CORS, Uvicorn settings)
│   ├── ingest_router.py            # API routing for social hooks & follow-ups
│   ├── db_manager.py               # SQLite relational manager & CRUD methods
│   ├── social_capture_engine.py    # Comment scanners, capture, and CRM registries
│   ├── crm_followup_engine.py      # Automated Follow-up Daemon (DM/WhatsApp Nudges)
│   ├── social_insights_connector.py# Platform simulation API adapters (IG, FB, YT)
│   ├── whatsapp_connector.py       # WhatsApp Business API REST adapters
│   ├── workflow.py                 # LangGraph StateGraph workflow engine
│   ├── conversion_engine.py        # Value-lift conversions calculations
│   ├── schema.sql                  # PostgreSQL layout blueprint
│   └── test_suite_runner.py        # Unified QA Testing suite (Smoke, Sanity, Load)
├── index.html                      # Glassmorphic SaaS Dashboard UI
├── dashboard.html                  # Telemetry analytics panel
└── mcp-servers.json                # Model Context Protocol servers configuration
```

---

## 7. Local Installation & Development

### 1. Configure the Environment
Copy `.env.example` into a secure `.env` file:
```bash
cp .env.example .env
```
Fill out your Meta Graph page access tokens, YouTube Data v3 API keys, and WhatsApp Phone ID credentials. If left blank, the system automatically falls back to secure **Simulation Mode** allowing immediate testing.

### 2. Boot the API Server
Start the Uvicorn webserver with auto-reload:
```bash
PYTHONPATH=. python3 backend/main.py
```
The server will boot on `http://localhost:8080`. API documentation is available at `http://localhost:8080/docs`.

### 3. Run the Automated QA Test Runner
Verify that the system meets enterprise SaaS performance requirements by running our unified testing runner:
```bash
PYTHONPATH=. python3 backend/test_suite_runner.py
```
This runs:
*   **Smoke Uptime Tests**: Validates FastAPI ping, database connection, and file paths.
*   **Sanity Flow Tests**: Registers a Reel, simulates comment `"ENROLL"`, checks prospect creation, and confirms ledger installment mapping.
*   **Service Audits**: Verifies connectors, ad optimizers, LangGraph, and follow-up engines individually.
*   **Load Stress Test**: Executes **150 parallel requests** to verify high-concurrency latencies (<50ms).

***

## 8. Global Deployments

*   👉 **Production Live Link**: [https://antigravity-ai-amber.vercel.app](https://antigravity-ai-amber.vercel.app)
*   **GitHub Repository**: [babuganesh5-wq/AI-dashboard](https://github.com/babuganesh5-wq/AI-dashboard.git)
