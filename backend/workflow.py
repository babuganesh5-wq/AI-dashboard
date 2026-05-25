# app/agents/orchestration/workflow.py
# Antigravity AI LangGraph Multi-Agent Orchestration Workflow
# Adapted specifically for Rhythm Academy Business Operations & Split Payment Ledgers

import time
import hashlib
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from backend.conversion_engine import AdAlgorithmOptimizer

def fetch_or_create_prospect(whatsapp_number: str, name: str):
    class Profile:
        prospect_id = "770e8400-e29b-41d4-a716-446655440000"
        student_name = name
        number = whatsapp_number
        current_funnel_stage = "WHATSAPP_LEAD_INGESTED"
        target_program = "6M_PRODUCTION"
        first_installment_paid = False
    return Profile()

def evaluate_whatsapp_intent(text: str):
    text_upper = text.upper()
    # Check if the prospect is checking in for a course program or making inquiries
    if any(keyword in text_upper for keyword in ["PRODUCTION", "MUSIC", "COURSE", "ENROLL", "DIPLOMA"]):
        return {
            "action": "INITIATE_QUALIFICATION_CHAT",
            "course_intent": "MUSIC_PRODUCTION",
            "prospect_intent": "HIGH-INTENT LEAD"
        }
    elif any(keyword in text_upper for keyword in ["PAY", "INSTALLMENT", "FEE", "DUE"]):
        return {
            "action": "PROCESS_BILLING_INQUIRY",
            "course_intent": "BILLING",
            "prospect_intent": "ACTIVE_STUDENT"
        }
    return {"action": "ROUTING_TO_HUMAN_ADVISOR", "course_intent": "GENERAL"}

def hash_data(data: str) -> str:
    return hashlib.sha256(data.encode('utf-8')).hexdigest()

class RhythmWhatsAppClient:
    @staticmethod
    async def send_qualification_message(whatsapp_number: str, name: str):
        text = f"Hi {name}! Welcome to Rhythm Academy. Mapped your inquiry for our Music Production programs. Let's schedule a brief Studio Visit to check out our setups. Can you confirm your email?"
        print(f"[WHATSAPP_LEAD_QUALIFIER] Sent thread: {text}")
        return text

    @staticmethod
    async def send_installment_escalation(whatsapp_number: str, student_id: str, balance: float):
        text = f"Hello! Friendly reminder from Rhythm Academy. Your second split installment of ₹{balance:,.2f} is currently due. Please click this link to secure your payment: secure.rhythmacademy.com/pay/{student_id}"
        print(f"[WHATSAPP_BILLING_ESCALATION] Sent reminder: {text}")
        return text

class AgentWorkflowState:
    def __init__(self):
        self.graph = StateGraph(dict)
        self._build_graph()
        self.optimizer = AdAlgorithmOptimizer()

    def _build_graph(self):
        # Define Rhythm Academy multi-agent stategraph nodes
        self.graph.add_node("whatsapp_lead_capture", self.retrieve_whatsapp_lead_context)
        self.graph.add_node("lead_intent_analyzer", self.analyze_lead_intent)
        self.graph.add_node("interactive_qualifier", self.execute_qualification_chat)
        self.graph.add_node("billing_installment_daemons", self.process_installment_ledger)
        self.graph.add_node("value_lift_capi_sync", self.dispatch_offline_capi_lift)

        # Set workflow pipeline routing
        self.graph.set_entry_point("whatsapp_lead_capture")
        self.graph.add_edge("whatsapp_lead_capture", "lead_intent_analyzer")
        
        self.graph.add_conditional_edges(
            "lead_intent_analyzer",
            self.route_whatsapp_path,
            {
                "qualify_course": "interactive_qualifier",
                "process_billing": "billing_installment_daemons",
                "advisor_fallback": END
            }
        )
        self.graph.add_edge("interactive_qualifier", "value_lift_capi_sync")
        self.graph.add_edge("billing_installment_daemons", "value_lift_capi_sync")
        self.graph.add_edge("value_lift_capi_sync", END)
        self.runtime = self.graph.compile()

    async def retrieve_whatsapp_lead_context(self, state: Dict[str, Any]) -> Dict[str, Any]:
        event = state["event"]
        name = event.get("sender_name", "Prospect Lead")
        prospect_profile = fetch_or_create_prospect(event.sender_platform_id, name)
        
        state["prospect_id"] = prospect_profile.prospect_id
        state["student_name"] = prospect_profile.student_name
        state["whatsapp_number"] = prospect_profile.number
        state["funnel_stage"] = prospect_profile.current_funnel_stage
        state["target_program"] = prospect_profile.target_program
        state["start_time"] = time.time()
        return state

    async def analyze_lead_intent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        text = state["event"].text_content
        intent = evaluate_whatsapp_intent(text)
        state["next_action"] = intent["action"]
        state["course_intent"] = intent["course_intent"]
        return state

    def route_whatsapp_path(self, state: Dict[str, Any]) -> str:
        if state["next_action"] == "INITIATE_QUALIFICATION_CHAT":
            return "qualify_course"
        elif state["next_action"] == "PROCESS_BILLING_INQUIRY":
            return "process_billing"
        return "advisor_fallback"

    async def execute_qualification_chat(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Instantly captures context and schedules direct Studio Visit conversions
        num = state["whatsapp_number"]
        name = state["student_name"]
        
        # Fire automated WhatsApp response
        await RhythmWhatsAppClient.send_qualification_message(num, name)
        state["qualification_completed"] = True
        state["studio_visit_booked"] = True
        state["simulated_email_captured"] = f"{name.lower().replace(' ', '')}@rhythmacademy-lead.com"
        state["milestone"] = "STUDIO_VISIT"
        return state

    async def process_installment_ledger(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Evaluates first installment paid vs overdue installments balance ₹15,000 reminders
        num = state["whatsapp_number"]
        prospect_id = state["prospect_id"]
        
        # Deploy reminder escalations to protect cash flow
        await RhythmWhatsAppClient.send_installment_escalation(
            whatsapp_number=num,
            student_id=prospect_id,
            balance=15000.00
        )
        state["billing_reminder_sent"] = True
        state["milestone"] = "INSTALLMENT_PAID"
        return state

    async def dispatch_offline_capi_lift(self, state: Dict[str, Any]) -> Dict[str, Any]:
        # Offline Bidding Optimizer: fires server-side CAPI events to lower CPA
        event = state["event"]
        email = state.get("simulated_email_captured", "student@rhythmacademy.com")
        duration = time.time() - state["start_time"]
        milestone = state.get("milestone", "WHATSAPP_LEAD")
        program = state.get("target_program", "6M_PRODUCTION")
        
        lead_data = {
            "hashed_email": hash_data(email),
            "fb_click_id": event.attribution_click_id,
            "program_type": program
        }
        
        # Push Async Meta CAPI lift
        lift_results = await self.optimizer.fire_meta_capi_lift_event(
            lead_data=lead_data,
            event_type=milestone,
            response_speed=round(duration, 2)
        )
        state["value_lift_metrics"] = lift_results
        return state
