# backend/test_suite_runner.py
# Antigravity AI - Production Uptime, Smoke, Sanity & Load Testing Suite
# Executes SaaS quality-assurance verification across all services

import os
import sys
import time
import json
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Force test database to avoid polluting main db
TEST_DB_PATH = os.path.join(os.path.dirname(__file__), "test_suite_antigravity.db")
os.environ["DATABASE_PATH"] = TEST_DB_PATH

from fastapi.testclient import TestClient
from backend.main import app
from backend.db_manager import db_manager
from backend.social_capture_engine import social_capture_engine
from backend.social_insights_connector import InstagramInsightsConnector
from backend.conversion_engine import AdAlgorithmOptimizer
from backend.workflow import AgentWorkflowState

client = TestClient(app)

class Color:
    GREEN = "\033[92m"
    RED = "\033[91m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def print_header(title):
    print(f"\n{Color.BOLD}{Color.CYAN}===================================================================={Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}   {title.upper()}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}===================================================================={Color.RESET}")

def print_result(name, passed, detail=""):
    status = f"{Color.GREEN}✓ PASSED{Color.RESET}" if passed else f"{Color.RED}✗ FAILED{Color.RESET}"
    print(f"[{status}] - {name} {f'({detail})' if detail else ''}")

# ==========================================
# 1. SMOKE TESTS (Basic Uptime & Connection)
# ==========================================
def run_smoke_tests():
    print_header("Smoke Testing Uptime")
    
    # 1.1 Server Root
    try:
        res = client.get("/")
        passed = res.status_code == 200 and res.json().get("status") == "online"
        print_result("FastAPI Server Root Ping", passed, f"Status: {res.status_code}")
    except Exception as e:
        print_result("FastAPI Server Root Ping", False, str(e))
        passed = False
        
    # 1.2 DB Connection
    try:
        # Initialize isolated test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        db_manager.__init__(db_path=TEST_DB_PATH)
        db_manager.init_db()
        
        with db_manager.get_connection() as conn:
            cursor = conn.execute("SELECT 1;")
            db_res = cursor.fetchone()
            passed_db = db_res is not None and db_res[0] == 1
        print_result("SQLite Relational DB Connectivity", passed_db)
    except Exception as e:
        print_result("SQLite Relational DB Connectivity", False, str(e))
        passed_db = False

    # 1.3 Static Files Existence
    files = ["index.html", "dashboard.html", "backend/main.py", "backend/workflow.py"]
    for f in files:
        ex = os.path.exists(f)
        print_result(f"File Existence Check: {f}", ex)
        
    return passed and passed_db

# ==========================================
# 2. SANITY TESTS (Specific Core Workflows)
# ==========================================
def run_sanity_tests():
    print_header("Sanity Testing Core Workflows")
    
    # 2.1 Social Content Registration
    try:
        res = client.post("/api/v1/social/content", params={
            "platform": "INSTAGRAM",
            "content_type": "REEL",
            "title": "Smoke Test Reel",
            "caption": "Sanity test running live",
            "post_url": "https://instagram.com/reel/smoke_test",
            "media_url": "https://cdn.rhythmacademy.com/smoke.mp4"
        })
        data = res.json()
        content_id = data.get("content_id")
        passed_reg = res.status_code == 200 and content_id is not None
        print_result("register_social_content Endpoint", passed_reg, f"ContentID: {content_id}")
    except Exception as e:
        print_result("register_social_content Endpoint", False, str(e))
        passed_reg = False
        content_id = None
        
    # 2.2 Comment Capture Simulation & Lead Conversion
    try:
        if content_id:
            res_sim = client.post("/api/v1/social/captures/simulate", params={
                "content_id": content_id,
                "commenter": "@sanity_tester_99",
                "text": "I want to ENROLL in the music production diploma course immediately!",
                "platform": "INSTAGRAM"
            })
            sim_data = res_sim.json()
            capture_res = sim_data.get("capture_result", {})
            passed_sim = res_sim.status_code == 200 and capture_res.get("status") == "captured"
            print_result("simulate_social_capture Endpoint", passed_sim, f"Keyword: {capture_res.get('keyword_matched')}")
            
            # Verify Prospect Creation
            prospect_id = capture_res.get("prospect_id")
            prospect = db_manager.get_prospect(prospect_id)
            # The capture engine capitalizes commenter handle handles to names:
            # "@sanity_tester_99" -> first_name: "Sanity", last_name: "Tester 99"
            passed_prospect = prospect is not None and prospect["first_name"] == "Sanity"
            print_result("Database Prospect Persistence", passed_prospect, f"Prospect First Name: {prospect['first_name'] if prospect else 'None'}")
            
            # Verify Ledger Installments Mapping (Query table directly)
            lead_id = capture_res.get("lead_id")
            with db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT * FROM Rhythm_Installments_Ledger WHERE lead_id = ?", (lead_id,))
                rows = cursor.fetchall()
                passed_ledger = len(rows) == 2
            print_result("Split Ledger Installments Creation", passed_ledger, f"Count: {len(rows)}")
        else:
            print_result("simulate_social_capture Endpoint", False, "Skipped due to registration failure")
            passed_sim = passed_prospect = passed_ledger = False
    except Exception as e:
        print_result("simulate_social_capture Endpoint", False, str(e))
        passed_sim = passed_prospect = passed_ledger = False
        
    return passed_reg and passed_sim and passed_prospect and passed_ledger

# ==========================================
# 3. INDIVIDUAL SERVICE TESTING
# ==========================================
def run_service_tests():
    print_header("Individual Service Verification")
    
    # 3.1 Platform Connector Service
    try:
        connector = InstagramInsightsConnector()
        metrics = asyncio.run(connector.fetch_reel_metrics("reel_123"))
        comments = asyncio.run(connector.fetch_reel_comments("reel_123"))
        passed_conn = metrics.get("views") > 0 and len(comments) > 0
        print_result("Instagram Insights Connector Service", passed_conn, f"Simulated views: {metrics.get('views')}")
    except Exception as e:
        print_result("Instagram Insights Connector Service", False, str(e))
        passed_conn = False

    # 3.2 Dynamic Value Lift Service (Optimizer)
    try:
        optimizer = AdAlgorithmOptimizer()
        val = asyncio.run(optimizer.calculate_value_lift("WHATSAPP_LEAD", 60.0, "DIPLOMA"))
        # Base (5000) * Fast multiplier (1.5) * Diploma booster (1.2) = 9000.00
        passed_opt = val == 9000.00
        print_result("Dynamic Value Lift Ad Optimizer Service", passed_opt, f"Value lift: ₹{val}")
    except Exception as e:
        print_result("Dynamic Value Lift Ad Optimizer Service", False, str(e))
        passed_opt = False

    # 3.3 Capture Engine Service
    try:
        # Seeding content to ensure DB has data for calculations
        db_manager.seed_social_demo_data()
        aggregated = social_capture_engine.get_aggregated_analytics()
        passed_eng = "overview" in aggregated and "platform_breakdown" in aggregated and "capture_funnel" in aggregated
        print_result("Social Capture Engine Analytics Service", passed_eng)
    except Exception as e:
        print_result("Social Capture Engine Analytics Service", False, str(e))
        passed_eng = False

    # 3.4 Multi-Agent StateGraph Workflow Service
    try:
        workflow = AgentWorkflowState()
        passed_wf = workflow.runtime is not None
        print_result("LangGraph Conversation StateGraph runtime", passed_wf)
    except Exception as e:
        print_result("LangGraph Conversation StateGraph runtime", False, str(e))
        passed_wf = False
        
    # 3.5 Relentless CRM Follow-Up Engine Service
    try:
        from backend.crm_followup_engine import crm_followup_engine
        res_followup = asyncio.run(crm_followup_engine.execute_all_followup_loops())
        passed_followup = res_followup.get("status") == "success" and "loops" in res_followup
        print_result("Relentless CRM Follow-Up Engine Service", passed_followup)
    except Exception as e:
        print_result("Relentless CRM Follow-Up Engine Service", False, str(e))
        passed_followup = False
        
    return passed_conn and passed_opt and passed_eng and passed_wf and passed_followup

# ==========================================
# 4. HIGH-CONCURRENCY LOAD TESTING
# ==========================================
def run_load_tests():
    print_header("High-Concurrency Load Testing")
    
    concurrent_requests = 150
    print(f"Dispatching {concurrent_requests} concurrent requests to /api/v1/social/analytics...")
    
    success_count = 0
    errors = 0
    latencies = []
    
    def worker():
        nonlocal success_count, errors
        start = time.time()
        try:
            res = client.get("/api/v1/social/analytics")
            latency = (time.time() - start) * 1000
            latencies.append(latency)
            if res.status_code == 200:
                success_count += 1
            else:
                errors += 1
        except Exception:
            errors += 1
            
    # Send requests in parallel using ThreadPool
    start_all = time.time()
    with ThreadPoolExecutor(max_workers=30) as executor:
        futures = [executor.submit(worker) for _ in range(concurrent_requests)]
        # Wait for all to complete
        for f in futures:
            f.result()
            
    total_duration = time.time() - start_all
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    throughput = concurrent_requests / total_duration
    
    passed_load = errors == 0 and avg_latency < 120.0
    
    print_result("Load Test Performance (Concurrency: 150)", passed_load, 
                 f"Success: {success_count}/{concurrent_requests}, Avg Latency: {avg_latency:.2f}ms, Throughput: {throughput:.1f} req/s")
    
    return passed_load

if __name__ == "__main__":
    print(f"\n{Color.BOLD}{Color.GREEN}🚀 BOOTING ANTIGRAVITY AI SAAS SYSTEM QA RUNNER...{Color.RESET}")
    
    smoke_ok = run_smoke_tests()
    sanity_ok = run_sanity_tests()
    services_ok = run_service_tests()
    load_ok = run_load_tests()
    
    print_header("Unified QA Report Summary")
    
    all_ok = smoke_ok and sanity_ok and services_ok and load_ok
    if all_ok:
        print(f"\n{Color.BOLD}{Color.GREEN}★★★ UNIFIED QA VERIFICATION STATUS: 100% PRODUCTION LEVEL SAAS COMPLIANT ★★★{Color.RESET}\n")
        # Clean up isolated db
        if os.path.exists(TEST_DB_PATH):
            try: os.remove(TEST_DB_PATH)
            except: pass
        sys.exit(0)
    else:
        print(f"\n{Color.BOLD}{Color.RED}⚠⚠⚠ UNIFIED QA VERIFICATION STATUS: CRITICAL FAILURE ENCOUNTERED ⚠⚠⚠{Color.RESET}\n")
        sys.exit(1)
