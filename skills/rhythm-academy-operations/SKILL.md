# Rhythm Academy Operations Skill - Developer Reference Manual

This custom skill documents the architecture, database designs, multi-agent pipelines, and testing frameworks embedded in the **Antigravity AI (Rhythm Academy Edition)** marketing and billing automation operating system. It serves as a step-by-step presentation guide for developers and system operators.

---

## 1. Project Purpose & Core Problems Solved

Rhythm Academy runs music production, audio engineering, and acoustic science programs. The academy faced two massive operational bottlenecks that threatened its profitability and growth:
1.  **Challenge A: Revenue Cash Flow Leakage**: Course fees are split into two installments of ₹15,000 each. Manually tracking due dates, follow-up frequencies, and payment statuses via WhatsApp led to high defaults and lost revenue.
2.  **Challenge B: Low-Precision Paid Campaigns**: Paid Meta and Google Ads generated raw leads, but the lack of server-side conversion feedbacks to ad auctions led to high customer acquisition costs (CPA) and low-quality lookalike audiences.

### The Antigravity AI Solution:
*   **relational CRM & Ledger**: Automatically logs WhatsApp inbound leads and tracks split installments (₹15,000 + ₹15,000) using a real-time SQL state.
*   **LangGraph stategraph**: Analyzes course interest, qualifies prospects, books Studio Visits, and schedules payment alerts.
*   **Asynchronous Value Lift Engine**: Connects conversion milestones (Studio Visit check-in, installment paid) straight to Meta CAPI and Google SmartBidding. Bids are automatically boosted by a **1.5x speed multiplier** for prospects contacted under 3 minutes to reward speed-to-lead.
*   **Google Auth Gatekeeper**: Locks dashboards behind secure OAuth selects and Opal/n8n format checks.

---

## 2. Directory & Component Architecture

The codebase is organized into modular, easily maintainable directory structures:

```
antigravity-ai/
│
├── index.html                 # Main visual panel (glassmorphic live CRM grid & React Flow nodes)
├── dashboard.html             # Tactical Mission Control (real-time telemetry loops & logs)
├── auto_sync.sh               # DevOps daemon (pre-commit secrets check & Vercel deployer)
│
└── backend/                   # Python & Relational SQL Blueprint Layer
    ├── main.py                # FastAPI server entrypoint (registers ingest routes & CORS)
    ├── schema.sql             # SQL relational blueprints (leads, split ledgers, batches)
    ├── db_manager.py          # SQLite database CRUD manager (real SQL persistence)
    ├── ingest_router.py       # REST API endpoints (HMAC meta webhooks & CRM triggers)
    ├── conversion_engine.py   # Value Lift conversions calculator (Meta CAPI & Google Offline)
    ├── workflow.py            # LangGraph Comment-to-DM stategraph workflow
    ├── whatsapp_connector.py  # WhatsApp Cloud REST API client (Direct & Template alerts)
    │
    ├── test_database.py       # DB QA automated SQLite CRUD test runner
    └── test_backend.py        # Backend QA automated unit & integration test runner
```

---

## 3. Relational Database Schema Mappings

The SQLite manager enforces the exact relational boundaries defined in `schema.sql`:

```
┌────────────────┐          ┌──────────────────────┐          ┌─────────────────────────────┐
│ CRM_Prospects  │ 1 ──── 1 │ Rhythm_Academy_Leads │ 1 ──── 2 │ Rhythm_Installments_Ledger  │
│ (funnel stage) │          │ (course program fit) │          │ (₹15,000 split status)      │
└────────────────┘          └──────────────────────┘          └─────────────────────────────┘
```

*   **`CRM_Prospects`**: Master registry. Integrates SHA-256 secure email/phone hashes for OpenSec. Funnel stages: `INQUIRY` ➡️ `QUALIFIED` ➡️ `CUSTOMER`.
*   **`Rhythm_Academy_Leads`**: Handles student course program fits (`3M_PRODUCTION`, `6M_PRODUCTION`, `DIPLOMA`, `MUSIC_SCHOOL`) and Studio Visit completion flags.
*   **`Rhythm_Installments_Ledger`**: Tracks split amounts (₹15,000 standard). Links status values (`PAID`, `PENDING`, `OVERDUE`) and records follow-up reminder tallies.
*   **`Rhythm_Batches_Faculty`**: Tracks double simultaneous batches (Batch Alpha & Batch Beta) mapped to active faculty slots.

---

## 4. Multi-Agent Stategraph Pipelines

The LangGraph workspace state machine manages prospect transitions asynchronously:

1.  **WhatsApp Capture**: Node checks if the contact number exists. If not, it creates a prospect and maps their platform identity.
2.  **Intent Analyzer**: Categorizes inquiry body (e.g. text containing "PRODUCTION" routes to Course Qualification, containing "FEE" routes to Billing).
3.  **Qualifier Node**: Dispatches WhatsApp template response, registers scheduled Studio Visit, and sets up the two split installments (₹15k + ₹15k) in SQL.
4.  **Billing Ledger Daemon**: Flags overdue installments and outbounds alert links via WhatsApp.
5.  **CAPI/Offline Sync**: Calculates dynamic INR values, maps speed modifiers, and pushes signals to ad platforms.

---

## 5. Developer Testing & Execution Guide

### Running Automated Test Suites
Prior to push deployments, run the QA validation harnesses:
1.  **Database CRUD Assertions**:
    ```bash
    PYTHONPATH=. python3 backend/test_database.py
    ```
2.  **FastAPI Webhooks & Workflow Integration Checks**:
    ```bash
    PYTHONPATH=. python3 backend/test_backend.py
    ```

### Production Synchronization & Deploy
Run the DevOps sync daemon:
```bash
./auto_sync.sh
```
*Forces pre-flight scanning, Git branches tagged staging commits, and Vercel cloud serverless deploys.*
