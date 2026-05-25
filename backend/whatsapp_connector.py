# backend/whatsapp_connector.py
# Antigravity AI - WhatsApp Business API Connector
# Drives Comment-to-DM triggers and Split Installments Ledger notifications for Rhythm Academy

import httpx
from typing import Dict, Any, List

class RhythmWhatsAppConnector:
    def __init__(self, token: str = None, phone_id: str = None):
        # Fallback to simulation if environment variables are not supplied
        self.token = token or "simulated_whatsapp_token_credential_hash"
        self.phone_id = phone_id or "simulated_phone_id_hash"
        self.api_url = f"https://graph.facebook.com/v18.0/{self.phone_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        self.is_simulated = (token is None or phone_id is None)

    async def send_text_message(self, to_number: str, text: str) -> Dict[str, Any]:
        """Sends a standard direct message to a prospect or student."""
        if self.is_simulated or "simulated" in self.token:
            print(f"[WHATSAPP_SIMULATOR] Direct text to {to_number}: {text}")
            return {
                "status": "success",
                "message_id": "sim_msg_direct_12345",
                "simulated": True,
                "recipient": to_number,
                "content": text
            }

        payload = {
            "messaging_product": "whatsapp",
            "to": to_number,
            "type": "text",
            "text": {
                "body": text
            }
        }

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.api_url, json=payload, headers=self.headers, timeout=10.0)
                return response.json()
            except Exception as e:
                return {"error": str(e), "status_code": 500}

    async def send_text_template(
        self, 
        to_number: str, 
        template_name: str, 
        parameters: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """
        Sends official approved Meta WhatsApp templates to prospects or students.
        Allows Ban-Safe interactive messaging.
        """
        if self.is_simulated or "simulated" in self.token:
            print(f"[WHATSAPP_SIMULATOR] Template '{template_name}' sent to {to_number} with parameters: {parameters}")
            return {
                "status": "success",
                "message_id": f"sim_msg_tpl_{template_name}_12345",
                "simulated": True,
                "recipient": to_number,
                "template": template_name,
                "params": parameters
            }

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
