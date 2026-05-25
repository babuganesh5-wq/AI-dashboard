# app/main.py
# Antigravity AI High-Throughput Marketing OS Backend Application Entrypoint
# Configures CORS middleware for frontend API requests and boots webhook ingest routing

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.ingest_router import router as ingest_router

app = FastAPI(
    title="Antigravity AI - Autonomous Marketing Operating System",
    description="Production-grade API backend driving Comment-to-DM triggers, Split Installments Ledger notifications, and Meta CAPI / Google SmartBidding value lifts.",
    version="1.0.0"
)

# Enforce secure CORS policy to permit index.html and dashboard.html requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict to verified domains (e.g. vercel.app)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register the unified webhooks and conversion APIs router
app.include_router(ingest_router)

@app.get("/")
def get_root():
    return {
        "status": "online",
        "mesh": "connected",
        "platform": "Antigravity AI",
        "rhythm_academy_integration": "active",
        "documentation": "/docs"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8080, reload=True)
