# Antigravity AI - Multi-Agent Swarm Orchestration & Routing Blueprint

This document details the multi-agent coordination protocol, LangGraph node structures, Model Context Protocol (MCP) server meshes, and execution guidelines for **Antigravity AI**.

---

## 📢 Swarm Execution Paradigm (TL;DR)

```
┌────────────────────────────────────────────────────────────────────────┐
│  1. AGENT WORKFLOWS = Managed by LangGraph StateGraph (workflow.py)    │
│  2. AUTOMATED SCHEDULING = Managed by Follow-up Daemon (crm_followup)  │
│  3. ENTERPRISE DATA CONNECTORS = Live platform adapters + simulators   │
│  4. TOOLING PROTOCOL = Model Context Protocol (MCP) Server Mesh        │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 👥 Agent Architecture & Roles

Antigravity AI divides cognitive responsibilities among specialized backend agent nodes and coordinator engines:

| Agent Node | Role / Responsibility | Trigger Hook | Underlying Script |
|------------|-----------------------|--------------|-------------------|
| **Comment Capture Agent** | Scans inbound social media comment webhooks, runs keyword matching filters. | Inbound webhook / `/captures/simulate` | `social_capture_engine.py` |
| **Platform DM Dispatcher** | Resolves user profile identities, checks platform type, routes native Direct Messages. | Keyword match positive | `social_insights_connector.py` |
| **Intent Analyzer Agent** | Assesses lead reply messages, runs semantic sentiment analysis to gauge program interest. | Inbound chat response | `workflow.py` |
| **Firecrawl Scraper Agent**| Crawls prospect/studio websites to extract bio details, DAW choices, and personal goals for custom pitch messaging. | Visual flow trigger / `/crm/firecrawl/scrape` | `firecrawl_connector.py` |
| **Installments Nudge Agent**| Monitors overdue split installment ledgers, tracks reminder tallies, schedules follow-ups. | Schedule cron daemon / `/followup` | `crm_followup_engine.py` |
| **CAPI Lift Optimizer** | Calculates conversion speed-to-lead value coefficients and fires offline signals to ad algorithms. | Lead status change to Qualified | `conversion_engine.py` |

---

## ⚙️ LangGraph State Machine & Flows

Rather than relying on brittle conditional scripts, customer qualification is handled by **LangGraph StateGraph runtimes** within `backend/workflow.py`:

### 📺 Organic Social Capture StateGraph

```
                  ┌───────────────────────────────┐
                  │ Inbound Social Comment Hook   │
                  └───────────────┬───────────────┘
                                  │
                                  ▼
                    [ social_comment_capture ]
                                  │
                                  ▼
                          Keyword Matched?
                           /            \
                       YES/              \NO
                         ▼                ▼
             [ auto_dm_dispatcher ]     [ END ]
                         │
                         ▼
             [ lead_intent_analyzer ]
                         │
                         ▼
             Create CRM Prospect / Lead
                         │
                         ▼
                      [ END ]
```

### 💬 Conversational Lead Nurturing StateGraph
Managed inside `workflow.py` to drive qualification parameters:
- `qualify_lead`: Evaluates lead intent variables using sentiment heuristics.
- `dispatch_qualification_message`: Dispatches WhatsApp template structures via the `WhatsAppConnector`.
- `process_installment_ledger`: Writes split payment records (₹15,000 + ₹15,000) inside the `Rhythm_Installments_Ledger` SQLite database table.
- `dispatch_offline_capi_lift`: Automatically invokes the `AdAlgorithmOptimizer` to dispatch server-side offline conversion value lift events.

---

## 🔌 Model Context Protocol (MCP) Server Mesh

The agent mesh leverages the Model Context Protocol configured inside `mcp-servers.json` to allow LLM agents to read and edit enterprise datastores:

### 1. `meta-graph-social` (`@modelcontextprotocol/server-meta-graph`)
- **Scope**: Direct Instagram DMs, Facebook comment streams, feed webhook payloads.
- **Agent Action**: Listens for keyword matches, posts template auto-DMs.

### 2. `youtube-data-social` (`@modelcontextprotocol/server-youtube`)
- **Scope**: Channel statistics lookup, subscription events tracking, YouTube Shorts registrations.
- **Agent Action**: Synchronizes views and likes metrics into local SQLite stores.

### 3. `n8n-automation-bridge` (`@modelcontextprotocol/server-n8n`)
- **Scope**: Interconnects external visual automation flows and database sync webhooks.
- **Agent Action**: Resolves webhook handshakes.

### 4. `postgres-memory` (`@modelcontextprotocol/server-postgres`)
- **Scope**: Reads and writes relational tables inside PostgreSQL database clusters.
- **Agent Action**: Offloads analytical tables for master records.

### 5. `google-sheets-ledger` (`@modelcontextprotocol/server-google-sheets`)
- **Scope**: Shared spreadsheets authentication and ledger synchronization.
- **Agent Action**: Updates shared financial rows when student installments clear.

---

## 🚨 Guidelines for AI Agents modifying this Project

1. **Simulated Fallback Principle**: Always write API connectors with a simulated fallback loop. If the target environment variables (e.g. `TWENTY_CRM_API_KEY`, `META_APP_SECRET`) are absent, log `[SIMULATION MODE]` and return randomized, realistic mock telemetry rather than failing.
2. **OpenSec Safety Protocol**: Never bypass the credentials gatekeepers on the frontend overlays or write raw key files to git. Run `auto_sync.sh` before pushes to guarantee no API keys are checked in.
3. **Database Concurrency Protection**: SQLite is prone to locks during concurrent load tests. Always wrap write operations inside `with db_manager.get_connection() as conn:` contexts and handle exceptions safely.
4. **Attribution Modeling**: Attribution values are modulated by response time coefficients (e.g., speed-to-lead <5m boosts CAPI value by 1.8x). Maintain these mathematical models inside `backend/conversion_engine.py`.
