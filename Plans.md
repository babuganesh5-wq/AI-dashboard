# Antigravity AI - Modular Architecture & OpenSec Blueprint

This document details the target modular component structure, operational execution milestones, and the **OpenSec (Open Security)** protocols implemented across the **Antigravity AI** platform. It provides a standardized framework to securely scale our integrations, plugins, and multi-agent workflows.

---

## 1. OpenSec (Open Security) Standards

To protect enterprise credentials, prevent data leakage, and ensure reliable webhook transactions, the codebase enforces four core OpenSec security protocols:

### A. Cryptographic Webhook Handshakes (HMAC SHA-256)
- **Problem**: Exposed webhooks are vulnerable to spoofing, potentially injecting fake prospects or corrupting ad auction target variables.
- **Protocol**: Meta webhooks (`/api/v1/webhooks/meta`) validate payload integrity via `x_hub_signature_256` headers. The FastAPI ingest router computes expected signatures using a local `META_APP_SECRET` and rejects unauthenticated payloads instantly with a `403 Forbidden` status.

### B. Pre-commit Key Scanner Daemon (`auto_sync.sh`)
- **Problem**: Accidental commits of API keys (OpenAI tokens, database credentials) to public remote repositories like GitHub.
- **Protocol**: Prior to staging or committing, the synchronization script scans the entire codebase for patterns matching OpenAI keys (`sk-proj-...`, `sk-...`), Meta credentials, and Homebrew python paths. If a pattern matches, the sync halts immediately with a `[SECURITY FAILURE]` warning and does not commit.

### C. Dashboard Credentials Gateway (Opal & n8n Token Validation)
- **Problem**: Directly exposed dashboards could allow unauthorized access to active ad auctions and billing ledgers.
- **Protocol**: Access to frontend interfaces is governed by glassmorphic Auth Gateway overlays. The interface enforces token format checks:
  - Opal tokens must start with `sk-opal-`.
  - n8n keys must start with `n8n_api_key_`.
  - Unauthorized formats are blocked, printing a secure validation error.

### D. CORS Middleware Protections
- **Problem**: Cross-site scripting (XSS) could hijack local browser contexts and send commands to the backend.
- **Protocol**: The FastAPI app (`backend/main.py`) implements restricted CORS policy middleware, ensuring only authorized origins can send API requests or post webhooks to the local port (`8080`).

---

## 2. Modular Directory Architecture

We organize our codebase into functional, easily decoupled layers:

```
antigravity-ai/
│
├── adopt-skills.md            # Adopted plugins manual (Stitch, DevTools, Science)
├── Plans.md                   # Modular component maps & OpenSec security guidelines
├── index.html                 # Main secure app shell (React Flow canvas workspace)
├── dashboard.html             # High-fidelity dashboard shell (Real-time live logger)
├── auto_sync.sh               # Sync daemon, keys scanner, and Vercel cloud deployer
├── .gitignore                 # Excludes local private credentials and python virtual envs
├── .env.example               # Environment variables template
│
└── backend/                   # Python & SQL code blueprints
    ├── main.py                # FastAPI server entrypoint (Port 8880, CORS, Ingest Router)
    ├── schema.sql             # SQL DB structure (Leads, Split Installments, Faculty Batches)
    ├── ingest_router.py       # High-throughput webhook endpoints (HMAC signature validator)
    ├── conversion_engine.py   # Value Lift conversions optimizer (Milestones, INR ₹ value lifts)
    ├── workflow.py            # LangGraph multi-agent Comment-to-DM stategraph workflow
    ├── ad_generator_node.py   # n8n ad creator agent node (KieAI API + Sheets logger)
    └── google_studio_engine.py# Gemini 2.5 Flash video deconstructor & JSON schema output
```

---

## 3. Operational Execution Milestones

### 📈 Phase 1: Local-Live Synchronization (Completed)
*   [x] Rebrand entire marketing OS to **Antigravity AI**.
*   [x] Implement secure OAuth / Token gatekeepers on both dashboard files.
*   [x] Establish local HTTP static server on port `8000` and API webhook uvicorn server on port `8080`.
*   [x] Automate pre-flight security keys check and push production builds globally to Vercel.

### 👥 Phase 2: CRM & Installments Automation (In Progress)
*   [ ] Connect WhatsApp Business API webhooks to log prospects automatically in `Rhythm_Academy_Leads`.
*   [ ] Set up cron triggers inside the installments node. When a student's split payment (₹15,000) remains outstanding, fire automated reminder links.
*   [ ] Update dashboard to show a live grid table listing due dates, payment statuses, and reminder tallies.

### 📣 Phase 3: Smart Targeting Bidding (Upcoming)
*   [ ] Connect conversion lift outputs directly with active Meta Ads API parameters.
*   [ ] Dynamically scale CPC bids according to response speed metrics to lower overall cost-per-acquisition (CPA).
*   [ ] Test offline conversion feeds using Google Ads sandbox API.

### 🎓 Phase 4: Batch & Faculty Matcher (Long-term)
*   [ ] Incorporate smart matching algorithms to balance student seats across Batch Alpha and Batch Beta.
*   [ ] Set up visual faculty calendars in `index.html` to prevent schedule clashes.
