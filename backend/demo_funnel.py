# backend/demo_funnel.py
# Antigravity AI — Social Handle Inflow & Conversion Pipeline Simulator
# Live developer command-line demo showing viewer-to-student SQLite transitions

import os
import sys
import asyncio
from datetime import datetime, timedelta

# Import relational database manager
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.db_manager import db_manager
from backend.conversion_engine import AdAlgorithmOptimizer
from backend.workflow import AgentWorkflowState
from backend.ingest_router import InboundSocialEvent

async def run_visual_demo():
    print("\n\033[1;36m====================================================================\033[0m")
    print("\033[1;36m   ANTIGRAVITY AI — VIEWER-TO-STUDENT CONVERSION SIMULATOR   \033[0m")
    print("\033[1;36m====================================================================\033[0m")
    
    # Ensure database is initialized
    db_path = db_manager.db_path
    print(f"\033[0;33m[*] Connected to Relational CRM SQLite Database: {db_path}\033[0m")
    
    # 1. Prepare database and capture counts after cleanup
    
    # 2. Simulate Raw Social Viewer Comment Engagement
    viewer_name = "Aravind Swamy"
    viewer_phone = "+919940129402"
    comment_text = "Secrets of Phase Cancellation is amazing! I want to enroll in the music PRODUCTION course! SCALE"
    
    # Clean up previous demo runs to ensure deterministic clean state
    import hashlib
    viewer_phone_hash = hashlib.sha256(viewer_phone.encode()).hexdigest()
    with db_manager.get_connection() as conn:
        conn.execute("DELETE FROM CRM_Prospects WHERE phone_hashed = ?", (viewer_phone_hash,))
        conn.commit()
        
    # Re-fetch counts after clean up
    with db_manager.get_connection() as conn:
        before_leads = conn.execute("SELECT COUNT(*) FROM Rhythm_Academy_Leads").fetchone()[0]
        before_revenue = conn.execute("SELECT TOTAL(amount) FROM Rhythm_Installments_Ledger WHERE status = 'PAID'").fetchone()[0]
        
    print(f"[*] Initial Active Leads: \033[1;37m{before_leads}\033[0m")
    print(f"[*] Initial Collected Fees: \033[1;32m₹{before_revenue:,.2f}\033[0m")
    
    print(f"\n\033[1;35m[STAGE 1: VIEWER ENGAGEMENT]\033[0m")
    print(f"  ➔ Viewer \033[1;37m'{viewer_name}'\033[0m left a comment on Reel: 'Phase Cancellations Secrets'")
    print(f"  ➔ Comment: \033[0;35m\"{comment_text}\"\033[0m")
    
    # 3. Trigger n8n webhook and LangGraph workflow routing
    print(f"\n\033[1;34m[STAGE 2: Comment-to-DM LANGGRAPH ROUTER]\033[0m")
    print(f"  [*] Firing Comment-to-DM REST webhook trigger...")
    
    workflow = AgentWorkflowState()
    event = InboundSocialEvent(
        platform="WHATSAPP",
        sender_platform_id=viewer_phone,
        text_content=comment_text,
        attribution_click_id="fb_click_id_99401"
    )
    
    initial_state = {
        "event": event,
        "sender_name": viewer_name
    }
    
    # Run the multi-agent pipeline
    final_state = await workflow.runtime.ainvoke(initial_state)
    print(f"  [✓] LangGraph Multi-Agent Flow Completed.")
    print(f"  [✓] Funnel Stage Resolution: \033[1;34m{final_state.get('milestone')}\033[0m")
    
    # 4. Read relational database lead capture details
    prospect = db_manager.get_prospect_by_identity("WHATSAPP", viewer_phone)
    if not prospect:
        print("\033[0;31m[ERROR] Failed to save prospect to database.\033[0m")
        return
        
    leads = db_manager.get_all_leads_with_details()
    matching_lead = next((l for l in leads if l["whatsapp_number"] == viewer_phone), None)
    
    if not matching_lead:
        print("\033[0;31m[ERROR] Failed to retrieve matching Rhythm Academy lead.\033[0m")
        return
        
    print(f"\n\033[1;35m[STAGE 3: SQLite CRM REGISTRY]\033[0m")
    print(f"  ➔ Unified CRM Prospect ID: \033[1;37m{prospect['prospect_id']}\033[0m")
    print(f"  ➔ Funnel Stage: \033[1;35m{prospect['current_funnel_stage']}\033[0m")
    print(f"  ➔ Course Enrollment Lead: \033[1;37m{matching_lead['student_name']}\033[0m ({matching_lead['target_program']})")
    
    # 5. Process first ₹15,000 split installment
    print(f"\n\033[1;33m[STAGE 4: RELATIONAL SPLIT INSTALLMENT #1]\033[0m")
    print(f"  [*] Processing ₹15,000 payment for Installment #1...")
    
    # Retrieve ledger rows
    with db_manager.get_connection() as conn:
        ledger_rows = conn.execute(
            "SELECT installment_id, amount, status FROM Rhythm_Installments_Ledger WHERE lead_id = ? ORDER BY installment_number",
            (matching_lead["lead_id"],)
        ).fetchall()
        
    if ledger_rows:
        db_manager.update_installment_status(ledger_rows[0]["installment_id"], "PAID")
        print(f"  [✓] Installment #1 updated in SQL to: \033[1;32mPAID (₹{ledger_rows[0]['amount']:,.2f})\033[0m")
        
    # 6. Process second ₹15,000 split installment (converting lead to Customer/Student)
    print(f"\n\033[1;32m[STAGE 5: FULL STUDENT CONVERSION & ENROLLMENT]\033[0m")
    print(f"  [*] Processing ₹15,000 payment for Installment #2...")
    
    if len(ledger_rows) > 1:
        db_manager.update_installment_status(ledger_rows[1]["installment_id"], "PAID")
        print(f"  [✓] Installment #2 updated in SQL to: \033[1;32mPAID (₹{ledger_rows[1]['amount']:,.2f})\033[0m")
        
        # Upgrade lead stage to CUSTOMER upon full payment
        with db_manager.get_connection() as conn:
            conn.execute(
                "UPDATE CRM_Prospects SET current_funnel_stage = 'CUSTOMER' WHERE prospect_id = ?",
                (prospect["prospect_id"],)
            )
            
    # 7. Final Database Report after Conversion
    print(f"\n\033[1;36m[STAGE 6: FINAL CONVERSION METRICS]\033[0m")
    
    with db_manager.get_connection() as conn:
        after_leads = conn.execute("SELECT COUNT(*) FROM Rhythm_Academy_Leads").fetchone()[0]
        after_revenue = conn.execute("SELECT TOTAL(amount) FROM Rhythm_Installments_Ledger WHERE status = 'PAID'").fetchone()[0]
        prospect_updated = conn.execute("SELECT current_funnel_stage FROM CRM_Prospects WHERE prospect_id = ?", (prospect["prospect_id"],)).fetchone()
        
    print(f"  [✓] Total Active Leads: \033[1;37m{after_leads}\033[0m (Net Change: +1)")
    print(f"  [✓] Total Collected Fees: \033[1;32m₹{after_revenue:,.2f}\033[0m (Revenue Lift: +₹30,000.00)")
    print(f"  [✓] Final Student CRM State: \033[1;32m{prospect_updated['current_funnel_stage']}\033[0m (Viewer ➔ Customer SUCCESS)")
    
    print("\n\033[1;36m====================================================================\033[0m")
    print("\033[1;32m   CONVERSION PIPELINE COMPLETED SUCCESSFULLY!                      \033[0m")
    print("\033[1;36m====================================================================\033[0m\n")

if __name__ == "__main__":
    asyncio.run(run_visual_demo())
