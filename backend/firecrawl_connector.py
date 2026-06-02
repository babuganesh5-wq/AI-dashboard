# backend/firecrawl_connector.py
# Antigravity AI - Firecrawl API Connector
# Web crawler and scraper helper to convert pages to clean markdown for lead enrichment

import httpx
import os
import random
from typing import Dict, Any

class FirecrawlConnector:
    """
    Adapter for Firecrawl API (open-source web crawler for LLM agents).
    Enriches prospects by scraping their websites or portfolios.
    Runs in simulation mode by default or live API mode if credentials are set.
    """

    def __init__(self, api_url: str = None, api_key: str = None):
        self.api_url = api_url or os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev/v0")
        self.api_key = api_key or os.getenv("FIRECRAWL_API_KEY", "simulated_firecrawl_key_hash")
        self.is_simulated = ("simulated" in self.api_key or not api_key and not os.getenv("FIRECRAWL_API_KEY"))
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def scrape_url(self, url: str) -> Dict[str, Any]:
        """
        Scrapes a URL using Firecrawl and returns clean markdown.
        """
        if not url:
            return {"status": "error", "message": "No URL provided for scraping."}

        if self.is_simulated:
            # Return high-fidelity mock crawled data based on URL context
            mock_markdown = f"""
# Webpage Scraped: {url}
## Bio & Portfolio
I am an indie music producer and audio engineer. I specialize in electronic music, synthwave, and trap beats. 
I have been producing for 3 years using Ableton Live and Logic Pro. I am looking to scale up my skills and join a professional music school.

## Skills & Gear
- DAW: Ableton Live 11, FL Studio 21
- Synthesizers: Serum, Vital, Juno-106 (Hardware)
- Interests: Mixing, Mastering, Vocal Tuning, Synthesizer Sound Design
            """
            return {
                "status": "success",
                "url": url,
                "title": "Home - Portfolio & Audio Work",
                "markdown": mock_markdown,
                "metadata": {
                    "author": "Indie Producer",
                    "description": "Electronic music production portfolio and services."
                },
                "simulated": True
            }

        # Live Firecrawl implementation
        endpoint = f"{self.api_url}/scrape"
        payload = {
            "url": url,
            "pageOptions": {
                "onlyMainContent": True
            }
        }
        async with httpx.AsyncClient() as client:
            try:
                res = await client.post(endpoint, json=payload, headers=self.headers, timeout=15.0)
                if res.status_code == 200:
                    return {
                        "status": "success",
                        "url": url,
                        "title": res.json().get("data", {}).get("metadata", {}).get("title", ""),
                        "markdown": res.json().get("data", {}).get("markdown", ""),
                        "metadata": res.json().get("data", {}).get("metadata", {}),
                        "simulated": False
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Firecrawl API returned status code {res.status_code}: {res.text}"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Firecrawl connection failed: {str(e)}"
                }

# Module-level instance
firecrawl_connector = FirecrawlConnector()
