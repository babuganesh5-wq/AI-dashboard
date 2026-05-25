# Antigravity AI - Plugins, Connectors & MCP Servers Integration Manifest

This integration manifest details the installation parameters, configuration JSON templates, and custom execution connectors required to register Model Context Protocol (MCP) servers and external API plugins within the **Antigravity AI** multi-agent environment.

---

## 1. Relational Memory Layer: PostgreSQL MCP Server

We adopt the official open-source PostgreSQL MCP server to allow cognitive agents to query lead directories, schedule double batches, and retrieve pgvector conversation histories using natural language.

### A. Installation Parameters
The server runs system-wide using Node.js (`npx`):
*   **Package**: `@modelcontextprotocol/server-postgres`
*   **Database Target**: `postgresql://postgres:postgres@localhost:5432/antigravity_db`

### B. Integration Configuration JSON
Add this configuration snippet to your client config file (e.g. `claude_desktop_config.json` or Project IDX plugins manager configuration):

```json
{
  "mcpServers": {
    "postgres-memory": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-postgres",
        "postgresql://postgres:postgres@localhost:5432/antigravity_db"
      ]
    }
  }
}
```

### C. Exposed Tools & Capabilities
*   `query`: Executes standard PostgreSQL queries (handles parameterized values to satisfy OpenSec regulations).
*   `describe_table`: Returns columns and types for `Rhythm_Academy_Leads` and `Rhythm_Installments_Ledger`.
*   `show_tables`: Lists all active tables in the memory space.

---

## 2. Installments Ledger: Google Sheets MCP Server

We integrate the Google Sheets MCP server to append split payment collections and reminder frequencies dynamically to shared spreadsheets.

### A. Installation & Authorization
*   **Package**: `@modelcontextprotocol/server-google-sheets`
*   **Prerequisites**: 
    1. Enable Google Sheets and Google Drive APIs inside the Google Cloud Console.
    2. Download your Service Account JSON file and save it locally as `/Users/ganeshbabu/.gemini/antigravity/scratch/antigravity-ai/secrets.json` (Verify it is ignored in `.gitignore`).

### B. Configuration JSON
```json
{
  "mcpServers": {
    "google-sheets-ledger": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-google-sheets"
      ],
      "env": {
        "GOOGLE_APPLICATION_CREDENTIALS": "/Users/ganeshbabu/.gemini/antigravity/scratch/antigravity-ai/secrets.json",
        "SPREADSHEET_ID": "your_rhythm_academy_ledger_spreadsheet_id_hash"
      }
    }
  }
}
```

### C. Exposed Capabilities
*   `append_row`: Appends a student first installment transaction (₹15,000) or a reminder escalation log.
*   `read_sheet`: Pulls total outstanding balances to calculate collected monthly fee volumes.

---

## 3. Communication Channel: WhatsApp Business API Connector

To transition from manual logs to automated capture and reminders, we deploy a production-grade WhatsApp Cloud REST connector.

### A. Meta Graph API Configuration
Ensure your local `.env` has these validated variables populated:
```env
WHATSAPP_TOKEN=your_meta_temporary_or_permanent_system_user_token
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_business_phone_number_identifier_hash
WHATSAPP_WABA_ID=your_whatsapp_business_account_identifier
```

### B. Python WhatsApp REST Connector (`backend/whatsapp_connector.py`)
Save the following class to execute REST messages and payment alerts:

```python
import httpx
from typing import Dict, Any

class RhythmWhatsAppConnector:
    def __init__(self, token: str, phone_id: str):
        self.token = token
        self.api_url = f"https://graph.facebook.com/v18.0/{phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

    async def send_text_template(
        self, 
        to_number: str, 
        template_name: str, 
        parameters: list
    ) -> Dict[str, Any]:
        """
        Sends official approved Meta WhatsApp templates to prospects or students.
        Allows Ban-Safe interactive messaging.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": "en_US"
                },
                "components": [{
                    "type": "body",
                    "parameters": parameters
                }]
            }
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=self.headers, timeout=10.0)
                return response.json()
            except Exception as e:
                return {"error": str(e), "status_code": 500}
```

---

## 4. Bidding Optimiser: Meta CAPI & Google Offline Bidding

To feed Dynamic Value Lifts into ad account auctions and lower your Cost-Per-Acquisition (CPA):
*   Exposes custom hooks in `backend/conversion_engine.py` connecting your leads milestones (Studio Visits completions, ₹15,000 split payments paid) to server-side endpoints.
*   **Adoption Guidelines**: Bidding optimizers require the official `META_SYSTEM_USER_TOKEN` and Google Ads OAuth secrets to be populated in `.env` to route conversion tokens safely.

---

## 5. Social Handle Inflow: Meta Graph API MCP Server

We integrate the Meta Graph API MCP server to allow cognitive agents to monitor views, parse high-intent comment trigger keywords, and initiate automated direct messages dynamically.

### A. Installation Parameters
The server runs system-wide using Node.js (`npx`):
*   **Package**: `@modelcontextprotocol/server-meta-graph`

### B. Exposed Tools & Capabilities
*   `ig_get_media_comments`: Fetches comment feeds from active Reels and Posts.
*   `ig_reply_to_comment`: Replies publicly to comments with marketing trigger hooks.
*   `ig_send_direct_message`: Launches secure Comment-to-DM conversations.

---

## 6. YouTube Shorts & Video Comments: YouTube Data MCP Server

We integrate the YouTube Data API MCP server to poll YouTube Shorts and video comments, analyze viewer engagement, and dispatch automated course links.

### A. Installation Parameters
The server runs system-wide using Node.js (`npx`):
*   **Package**: `@modelcontextprotocol/server-youtube`

### B. Exposed Tools & Capabilities
*   `yt_get_video_comments`: Scans comment lists for trigger keywords (`LEAD`, `GROWTH`).
*   `yt_insert_comment_reply`: Replies to comments on Shorts and videos.
*   `yt_get_channel_analytics`: Pulls views, click-throughs, and retention statistics.

---

## 7. Workflow Handshakes: n8n Automation Bridge MCP Server

To bridge the gap between social comments and immediate out-of-band follow-ups (WhatsApp, SMS), we deploy the n8n automation bridge.

### A. Installation Parameters
The server runs system-wide using Node.js (`npx`):
*   **Package**: `@modelcontextprotocol/server-n8n`

### B. Exposed Tools & Capabilities
*   `trigger_workflow`: Fires pre-mapped n8n workflow triggers (such as SMS callbacks or Gmail registries) with custom data payloads.

