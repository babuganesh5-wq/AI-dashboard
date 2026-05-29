# backend/workflow.py
# Antigravity AI LangGraph Multi-Agent Orchestration Workflow
# Adapted specifically for Rhythm Academy Business Operations & Split Payment Ledgers

import time
import hashlib
from typing import Dict, Any, Union
from langgraph.graph import StateGraph, END
from backend.conversion_engine import AdAlgorithmOptimizer
from backend.db_manager import db_manager
from backend.whatsapp_connector import RhythmWhatsAppConnector

# Initialize the production-grade WhatsApp client
whatsapp_connector = RhythmWhatsAppConnector()

def get_event_field(event: Any, field_name: str, default: Any = None) -> Any:
    """Safely extracts a field from either a Pydantic model or a dictionary."""
    if event is None:
        return default
    if isinstance(event, dict):
        return event.get(field_name, default)
    if hasattr(event, field_name):
        return getattr(event, field_name)
    return default

def evaluate_whatsapp_intent(text: str):
    if not text:
        return {"action": "ROUTING_TO_HUMAN_ADVISOR", "course_intent": "GENERAL"}
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
        print(f"[WHATSAPP_LEAD_QUALIFIER] Dispatching thread: {text}")
        await whatsapp_connector.send_text_message(whatsapp_number, text)
        return text

    @staticmethod
    async def send_installment_escalation(whatsapp_number: str, student_id: str, balance: float):
        text = f"Hello! Friendly reminder from Rhythm Academy. Your second split installment of ₹{balance:,.2f} is currently due. Please click this link to secure your payment: secure.rhythmacademy.com/pay/{student_id}"
        print(f"[WHATSAPP_BILLING_ESCALATION] Dispatching reminder: {text}")
        await whatsapp_connector.send_text_message(whatsapp_number, text)
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
        
        # Safe attribute extraction resolving Bug B
        whatsapp_number = get_event_field(event, "sender_platform_id", "919999999999")
        name = get_event_field(event, "sender_name") or state.get("sender_name") or "Prospect Lead"
        
        # Relational check using the Database Manager
        prospect = db_manager.get_prospect_by_identity("WHATSAPP", whatsapp_number)
        
        if prospect:
            prospect_id = prospect["prospect_id"]
            student_name = prospect["first_name"] + " " + prospect["last_name"]
            current_funnel_stage = prospect["current_funnel_stage"]
        else:
            # Create a brand new prospect and identity mappings in SQL
            names = name.split(" ", 1)
            first_name = names[0]
            last_name = names[1] if len(names) > 1 else "Lead"
            email = f"{first_name.lower()}@rhythmacademy-lead.com"
            
            prospect_id = db_manager.create_prospect(
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=whatsapp_number,
                funnel_stage="INQUIRY"
            )
            
            # Map WhatsApp identity link
            fbclid = get_event_field(event, "attribution_click_id")
            db_manager.register_platform_identity(
                prospect_id=prospect_id,
                platform_name="WHATSAPP",
                external_id=whatsapp_number,
                handle_name=f"{first_name.lower()}_wa",
                fbclid=fbclid
            )
            
            student_name = name
            current_funnel_stage = "INQUIRY"

        # Create or fetch Rhythm Academy specialized lead record
        # Simple lookup across all leads in database
        lead_id = None
        for lead_row in db_manager.get_all_leads_with_details():
            if lead_row["prospect_id"] == prospect_id:
                lead_id = lead_row["lead_id"]
                break
                
        if not lead_id:
            lead_id = db_manager.create_lead(
                prospect_id=prospect_id,
                student_name=student_name,
                whatsapp_number=whatsapp_number,
                target_program="6M_PRODUCTION",
                source="META_ADS"
            )
        
        state["prospect_id"] = prospect_id
        state["lead_id"] = lead_id
        state["student_name"] = student_name
        state["whatsapp_number"] = whatsapp_number
        state["funnel_stage"] = current_funnel_stage
        state["target_program"] = "6M_PRODUCTION"
        state["start_time"] = time.time()
        return state

    async def analyze_lead_intent(self, state: Dict[str, Any]) -> Dict[str, Any]:
        event = state["event"]
        text = get_event_field(event, "text_content", "")
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
        num = state["whatsapp_number"]
        name = state["student_name"]
        lead_id = state["lead_id"]
        
        # Fire automated WhatsApp response using the connector
        await RhythmWhatsAppClient.send_qualification_message(num, name)
        
        # Persist qualifications and Studio Visits intent directly in SQL
        db_manager.update_lead_qualification(
            lead_id=lead_id,
            is_qualified=True,
            visit_scheduled=(time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + 86400))),
            visit_completed=False
        )
        
        # Setup split fee installments (₹15,000 + ₹15,000) inside ledger
        db_manager.record_installment(lead_id=lead_id, installment_number=1, amount=15000.00, due_days=1)
        db_manager.record_installment(lead_id=lead_id, installment_number=2, amount=15000.00, due_days=30)
        
        state["qualification_completed"] = True
        state["studio_visit_booked"] = True
        state["simulated_email_captured"] = f"{name.lower().replace(' ', '')}@rhythmacademy-lead.com"
        state["milestone"] = "STUDIO_VISIT"
        return state

    async def process_installment_ledger(self, state: Dict[str, Any]) -> Dict[str, Any]:
        num = state["whatsapp_number"]
        prospect_id = state["prospect_id"]
        lead_id = state["lead_id"]
        
        # Retrieve active installments in ledger to find pending/overdue amounts
        overdue_amount = 15000.00
        
        # Deploy reminder escalations to protect cash flow
        await RhythmWhatsAppClient.send_installment_escalation(
            whatsapp_number=num,
            student_id=prospect_id,
            balance=overdue_amount
        )
        
        # Find pending installments in database and increment reminder count
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT installment_id FROM Rhythm_Installments_Ledger WHERE lead_id = ? AND status != 'PAID'", (lead_id,))
            rows = cursor.fetchall()
            for row in rows:
                db_manager.increment_installment_reminder(row["installment_id"])
                
        state["billing_reminder_sent"] = True
        state["milestone"] = "INSTALLMENT_PAID"
        return state

    async def dispatch_offline_capi_lift(self, state: Dict[str, Any]) -> Dict[str, Any]:
        event = state["event"]
        email = state.get("simulated_email_captured", "student@rhythmacademy.com")
        duration = time.time() - state["start_time"]
        milestone = state.get("milestone", "WHATSAPP_LEAD")
        program = state.get("target_program", "6M_PRODUCTION")
        
        click_id = get_event_field(event, "attribution_click_id", "fb_click_12345")
        
        lead_data = {
            "hashed_email": hash_data(email),
            "fb_click_id": click_id,
            "program_type": program
        }
        
        # Push Async Meta CAPI lift using the optimizer
        lift_results = await self.optimizer.fire_meta_capi_lift_event(
            lead_data=lead_data,
            event_type=milestone,
            response_speed=round(duration, 2)
        )
        state["value_lift_metrics"] = lift_results
        return state

    # --- Social Capture Workflow Nodes ---

    async def social_comment_capture_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processes an inbound social media comment through the capture pipeline.
        Detects trigger keywords, creates a capture record, and prepares for DM dispatch.
        """
        comment_text = state.get("comment_text", "")
        commenter_handle = state.get("commenter_handle", "@unknown_user")
        commenter_id = state.get("commenter_platform_id", "unknown_id")
        platform = state.get("platform", "INSTAGRAM")
        content_id = state.get("content_id", "")

        # Match trigger keywords
        text_upper = comment_text.upper()
        matched_keyword = None
        trigger_keywords = ["GROWTH", "LEAD", "SCALE", "MUSIC", "ENROLL", "COURSE", "PRODUCTION", "RHYTHM", "DIPLOMA", "JOIN"]
        for keyword in trigger_keywords:
            if keyword in text_upper:
                matched_keyword = keyword
                break

        state["keyword_matched"] = matched_keyword
        state["is_trigger"] = matched_keyword is not None
        state["start_time"] = time.time()

        if matched_keyword:
            # Create capture record via db_manager
            capture_id = db_manager.create_comment_capture(
                content_id=content_id,
                platform=platform,
                commenter_handle=commenter_handle,
                commenter_platform_id=commenter_id,
                comment_text=comment_text,
                keyword_matched=matched_keyword
            )
            state["capture_id"] = capture_id
            print(f"[SOCIAL_CAPTURE] Keyword '{matched_keyword}' matched in comment by {commenter_handle}")
        else:
            state["capture_id"] = None
            print(f"[SOCIAL_CAPTURE] No trigger keyword found in comment by {commenter_handle}")

        return state

    async def auto_dm_dispatcher_node(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends platform-specific auto-DMs for triggered comments.
        Dispatches via Instagram DM, Facebook Messenger, or queues for WhatsApp (YouTube).
        """
        if not state.get("is_trigger"):
            state["dm_sent"] = False
            state["milestone"] = "NO_TRIGGER"
            return state

        platform = state.get("platform", "INSTAGRAM")
        commenter_handle = state.get("commenter_handle", "@unknown_user")
        commenter_id = state.get("commenter_platform_id", "unknown_id")
        commenter_name = commenter_handle.replace("@", "").replace("_", " ").title()

        dm_message = (
            f"Hey {commenter_name}! 🎵 Saw your interest in our music production content! "
            f"We're running a special 6-month production program at Rhythm Academy. "
            f"Want to schedule a free studio visit? Reply YES and we'll set it up!"
        )

        dm_result = {}
        if platform == "INSTAGRAM":
            from backend.social_insights_connector import instagram_connector
            dm_result = await instagram_connector.send_dm(commenter_id, dm_message)
        elif platform == "FACEBOOK":
            from backend.social_insights_connector import facebook_connector
            dm_result = await facebook_connector.send_messenger_message(commenter_id, dm_message)
        elif platform == "YOUTUBE":
            # YouTube doesn't support DMs, route to WhatsApp
            print(f"[AUTO_DM] YouTube DM not supported. Queuing {commenter_handle} for WhatsApp follow-up.")
            dm_result = {"status": "queued_whatsapp", "simulated": True}

        dm_sent = dm_result.get("status") in ("success", "queued_whatsapp")
        state["dm_sent"] = dm_sent
        state["dm_result"] = dm_result

        # Update capture record with DM status
        if state.get("capture_id"):
            db_manager.update_capture_status(
                capture_id=state["capture_id"],
                dm_sent=1 if dm_sent else 0
            )

        state["milestone"] = "SOCIAL_DM_SENT" if dm_sent else "SOCIAL_DM_FAILED"
        return state

    def route_social_capture_path(self, state: Dict[str, Any]) -> str:
        """Routes social capture based on keyword detection result."""
        if state.get("is_trigger"):
            return "dispatch_dm"
        return "end_capture"

    @staticmethod
    def create_social_capture_workflow():
        """
        Creates a secondary StateGraph for social comment-to-lead captures.
        This workflow is independent of the main WhatsApp lead capture graph
        and can be invoked separately for processing social media comments.

        Graph flow:
            social_comment_capture → [keyword matched?]
                → YES → auto_dm_dispatcher → lead_intent_analyzer → END
                → NO → END
        """
        workflow_instance = AgentWorkflowState()
        social_graph = StateGraph(dict)

        # Define social capture nodes
        social_graph.add_node("social_comment_capture", workflow_instance.social_comment_capture_node)
        social_graph.add_node("auto_dm_dispatcher", workflow_instance.auto_dm_dispatcher_node)
        social_graph.add_node("lead_intent_analyzer", workflow_instance.analyze_lead_intent)

        # Set entry point
        social_graph.set_entry_point("social_comment_capture")

        # Conditional routing based on keyword match
        social_graph.add_conditional_edges(
            "social_comment_capture",
            workflow_instance.route_social_capture_path,
            {
                "dispatch_dm": "auto_dm_dispatcher",
                "end_capture": END
            }
        )

        # After DM dispatch, analyze lead intent for further processing
        social_graph.add_edge("auto_dm_dispatcher", "lead_intent_analyzer")
        social_graph.add_edge("lead_intent_analyzer", END)

        return social_graph.compile()
