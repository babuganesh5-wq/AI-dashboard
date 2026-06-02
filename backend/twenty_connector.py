# backend/twenty_connector.py
# Antigravity AI - Twenty CRM API Connector (Salesforce Open Source Alternative)
# Maps SQLite CRM Prospects & Leads to Twenty CRM Workspace schema

import httpx
import os
import random
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.db_manager import db_manager

class TwentyCRMConnector:
    """
    Adapter for Twenty CRM (open-source Salesforce alternative).
    Allows syncing local prospects and leads to a central AI-centric CRM.
    Runs in simulation mode by default or live API mode if credentials are set.
    """

    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or os.getenv("TWENTY_CRM_API_URL", "https://api.twenty.com/v1")
        self.api_key = api_key or os.getenv("TWENTY_CRM_API_KEY", "simulated_twenty_crm_key_hash")
        self.is_simulated = ("simulated" in self.api_key or not api_key and not os.getenv("TWENTY_CRM_API_KEY"))
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def sync_prospect_to_twenty(self, prospect_id: str) -> Dict[str, Any]:
        """
        Creates or updates a Contact in Twenty CRM for a given SQLite Prospect ID.
        Returns the external Twenty CRM ID and sync status.
        """
        prospect = db_manager.get_prospect(prospect_id)
        if not prospect:
            return {"status": "error", "message": f"Prospect {prospect_id} not found in SQLite."}

        first_name = prospect.get("first_name") or "Prospect"
        last_name = prospect.get("last_name") or "User"
        email = f"prospect_{prospect_id[:8]}@rhythm.academy"
        phone = "+15555555555"

        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT student_name, whatsapp_number FROM Rhythm_Academy_Leads WHERE prospect_id = ?", (prospect_id,))
            lead_row = cursor.fetchone()
            if lead_row:
                name_parts = lead_row["student_name"].split(" ", 1)
                first_name = name_parts[0]
                if len(name_parts) > 1:
                    last_name = name_parts[1]
                phone = lead_row["whatsapp_number"]
                email = f"{first_name.lower()}.{last_name.lower()}@rhythm.academy".replace(" ", "")

        stage = prospect.get("current_funnel_stage", "INQUIRY")

        # Map funnel stages to Twenty CRM standard stages
        twenty_stage_mapping = {
            "INQUIRY": "NEW",
            "QUALIFIED": "CONTACTED",
            "CUSTOMER": "CUSTOMER",
            "LOST": "ARCHIVED"
        }
        mapped_stage = twenty_stage_mapping.get(stage, "NEW")

        payload = {
            "name": {
                "firstName": first_name,
                "lastName": last_name
            },
            "emails": [{
                "primary": True,
                "email": email,
                "label": "Work"
            }],
            "phones": [{
                "primary": True,
                "number": phone,
                "label": "Mobile"
            }],
            "lifecycleStage": mapped_stage,
            "createdBy": "ANTIGRAVITY_AI_AGENT"
        }

        if self.is_simulated:
            # Simulate a successful creation/update in Twenty CRM
            twenty_id = f"tw_cnt_{random.randint(100000, 999999)}"
            print(f"[TWENTY_CRM_SIMULATOR] Sync Contact: {first_name} {last_name} ({email}) -> Twenty ID: {twenty_id}")
            return {
                "status": "success",
                "twenty_contact_id": twenty_id,
                "synced_at": datetime.now().isoformat(),
                "simulated": True,
                "payload_sent": payload
            }

        # Live Twenty API implementation (Contacts endpoint)
        endpoint = f"{self.api_url}/contacts"
        async with httpx.AsyncClient() as client:
            try:
                # Search if contact already exists by email
                search_res = await client.get(
                    f"{endpoint}?filter[emails][email][eq]={email}",
                    headers=self.headers,
                    timeout=10.0
                )
                existing = search_res.json().get("data", [])
                
                if existing:
                    # Update contact
                    contact_id = existing[0]["id"]
                    res = await client.patch(f"{endpoint}/{contact_id}", json=payload, headers=self.headers, timeout=10.0)
                    return {
                        "status": "success",
                        "twenty_contact_id": contact_id,
                        "action": "update",
                        "response": res.json()
                    }
                else:
                    # Create contact
                    res = await client.post(endpoint, json=payload, headers=self.headers, timeout=10.0)
                    return {
                        "status": "success",
                        "twenty_contact_id": res.json().get("data", {}).get("id"),
                        "action": "create",
                        "response": res.json()
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Twenty CRM Connection Failed: {str(e)}",
                    "fallback_simulated": True,
                    "twenty_contact_id": f"tw_cnt_fallback_{random.randint(10000, 99999)}"
                }

    async def sync_lead_opportunity(self, lead_id: str) -> Dict[str, Any]:
        """
        Syncs a Rhythm Academy Lead to an Opportunity in Twenty CRM.
        Maps the split installments ledger values to the opportunity value.
        """
        lead = db_manager.get_lead(lead_id)
        if not lead:
            return {"status": "error", "message": f"Lead {lead_id} not found."}

        # Calculate opportunity value from installments
        value = 0.0
        paid_count = 0
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT SUM(amount) as total FROM Rhythm_Installments_Ledger WHERE lead_id = ?", (lead_id,))
            row = cursor.fetchone()
            if row and row["total"]:
                value = row["total"]
                
            cursor = conn.execute("SELECT COUNT(*) as paid FROM Rhythm_Installments_Ledger WHERE lead_id = ? AND status = 'PAID'", (lead_id,))
            count_row = cursor.fetchone()
            if count_row:
                paid_count = count_row["paid"]

        payload = {
            "name": f"Enrollment - {lead['student_name']}",
            "amount": value,
            "stage": "CLOSED_WON" if paid_count >= 2 else "PROPOSAL",
            "closeDate": datetime.now().isoformat(),
            "leadSource": lead.get("lead_source", "META_ADS")
        }

        if self.is_simulated:
            opp_id = f"tw_opp_{random.randint(100000, 999999)}"
            print(f"[TWENTY_CRM_SIMULATOR] Sync Opportunity: {lead['student_name']} (₹{value:,.2f}) -> Opportunity ID: {opp_id}")
            return {
                "status": "success",
                "twenty_opportunity_id": opp_id,
                "synced_at": datetime.now().isoformat(),
                "simulated": True,
                "payload_sent": payload
            }

        endpoint = f"{self.api_url}/opportunities"
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(endpoint, json=payload, headers=self.headers, timeout=10.0)
                return {
                    "status": "success",
                    "twenty_opportunity_id": res.json().get("data", {}).get("id"),
                    "action": "create",
                    "response": res.json()
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Twenty CRM Connection Failed: {str(e)}",
                    "fallback_simulated": True,
                    "twenty_opportunity_id": f"tw_opp_fallback_{random.randint(10000, 99999)}"
                }

# Module-level instance
twenty_connector = TwentyCRMConnector()
