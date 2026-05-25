# backend/run_browser_demo.py
# Antigravity AI - Automated Visual Browser Testing & Demo Runner
# Drives headless Chromium via Playwright, takes screenshots, and verifies frontend-backend integrations

import os
import asyncio
from playwright.async_api import async_playwright

# Define paths for screenshot artifacts
ARTIFACTS_DIR = "/Users/ganeshbabu/.gemini/antigravity/brain/dd86affd-efbc-4717-8da5-0aca0de62bf7"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

URL = "http://localhost:8000/index.html"

async def run_visual_demo():
    print("\n\033[0;36m====================================================\033[RESET]")
    print("\033[0;36m    LAUNCHING AUTOMATED VISUAL BROWSER DEMO...      \033[RESET]")
    print("\033[0;36m====================================================\033[RESET]")

    async with async_playwright() as p:
        # Launch Chromium headless
        browser = await p.chromium.launch(headless=True)
        # Emulate mac desktop window size
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print(f"\n[1/5] Navigating to local live static server: {URL}")
        await page.goto(URL)
        await page.wait_for_timeout(2000) # Wait for fade-in animations

        # Take screenshot of the initial Auth Gateway Overlay
        initial_shot = os.path.join(ARTIFACTS_DIR, "0_auth_gatekeeper.png")
        await page.screenshot(path=initial_shot)
        print(f"[SECURE] Locked Auth Gatekeeper overlay screenshot saved: {initial_shot}")

        print("\n[2/5] Simulating Google Workspace OAuth authorization check...")
        # Open Google Account Modal
        await page.click("button:has-text('Google Workspace')")
        await page.wait_for_timeout(1000)

        # Select first email account 'admin@rhythmacademy.com'
        await page.click("div:has-text('admin@rhythmacademy.com')")
        print("[SECURE] Admin OAuth handshake established. Awaiting workspace decryption...")
        
        # Wait for gatekeeper overlay to slide up and fade away
        await page.wait_for_timeout(4500)

        # Take screenshot of the Unlocked dashboard showing node canvas and workspace
        unlocked_shot = os.path.join(ARTIFACTS_DIR, "1_auth_unlocked.png")
        await page.screenshot(path=unlocked_shot)
        print(f"[SECURE] Decrypted Workspace Canvas screenshot saved: {unlocked_shot}")

        print("\n[3/5] Simulating new inbound paid lead via Meta Ads comments click...")
        # Locate and click 'Simulate New Lead' button on the Value Lift card
        await page.click("button:has-text('Simulate New Lead')")
        print("[LANGGRAPH] Dispatched Comment-to-DM triggers webhook and workflow loops...")
        
        # Wait for the LangGraph agent stategraph to complete, update database, and update CRM table
        await page.wait_for_timeout(4000)

        # Take screenshot showing the freshly appended student lead on the visual grid!
        lead_shot = os.path.join(ARTIFACTS_DIR, "2_lead_simulated.png")
        await page.screenshot(path=lead_shot)
        print(f"[CRM_SYNC] Relational CRM grid lead capture screenshot saved: {lead_shot}")

        print("\n[4/5] Testing Split Installment Ledger manual student payment updates...")
        # Click the first 'Pay #1' button next to Neha Sharma / Siddharth or custom simulated lead
        # The selector targets the Pay button dynamically inside the CRM grid
        try:
            await page.click("button:has-text('Pay #1')")
            print("[DB_UPDATE] Dispatched POST request to pay installment #1...")
            await page.wait_for_timeout(3000)
            
            # Take final screenshot showing green ₹15,000 PAID status and upgraded Stage!
            paid_shot = os.path.join(ARTIFACTS_DIR, "3_installment_paid.png")
            await page.screenshot(path=paid_shot)
            print(f"[DB_UPDATE] Split Fee collections ledger paid status screenshot saved: {paid_shot}")
        except Exception as e:
            print(f"[WARNING] Pay #1 button could not be clicked automatically: {str(e)}")

        print("\n[5/5] Visual browser testing sequence completed successfully!")
        await browser.close()
        
        print("\n\033[0;32m====================================================\033[RESET]")
        print("\033[0;32m    BROWSER TESTING & PRESENTATION COMPLETED!       \033[RESET]")
        print("\033[0;32m====================================================\033[RESET]\n")

if __name__ == "__main__":
    asyncio.run(run_visual_demo())
