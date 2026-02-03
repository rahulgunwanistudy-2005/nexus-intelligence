import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, BrowserContext
from loguru import logger

# Import the validated settings
from src.utils.config_loader import settings

class NexusScraper:
    """
    Ingestion Engine for the Nexus Pipeline.
    Responsibility: Fetch raw data and persist to the Bronze Layer (Immutable).
    """

    def __init__(self):
        self.cfg = settings.scraper
        self.paths = settings.paths
        
        # Ensure Bronze layer exists
        self.bronze_path = Path(self.paths.bronze)
        self.bronze_path.mkdir(parents=True, exist_ok=True)

    async def _create_context(self, p) -> BrowserContext:
        """Launches browser with stealth settings."""
        browser = await p.chromium.launch(headless=self.cfg.headless)
        context = await browser.new_context(
            user_agent=self.cfg.user_agent,
            viewport={"width": 1280, "height": 720},
            locale="en-IN"
        )
        return context

    async def run_extraction(self, query: str = None) -> Path:
        """
        Main execution method.
        
        Args:
            query (str): Optional override for search term.
            
        Returns:
            Path: The file path of the saved raw HTML.
        """
        search_term = query or self.cfg.search_term
        
        async with async_playwright() as p:
            context = await self._create_context(p)
            page = await context.new_page()
            
            logger.info(f"🚀 Starting Bronze Ingestion for: '{search_term}'")
            
            try:
                # 1. Build URL
                url = f"{self.cfg.base_url}/s?k={search_term.replace(' ', '+')}"
                
                # 2. Navigate with resilience
                response = await page.goto(url, timeout=self.cfg.timeout_ms)
                await page.wait_for_load_state("domcontentloaded")
                
                if response.status != 200:
                    logger.warning(f"⚠️ Non-200 Status Code: {response.status}")

                # 3. Extract Raw Content (The Bronze Layer)
                content = await page.content()
                
                # 4. Save to Disk
                save_path = self._save_bronze(content, search_term)
                logger.success(f"✅ Bronze Layer Ingestion Complete: {save_path.name}")
                return save_path

            except Exception as e:
                logger.error(f"❌ Ingestion Failed: {e}")
                raise e
            finally:
                await context.close()

    def _save_bronze(self, content: str, tag: str) -> Path:
        """
        Persists raw HTML to the Data Lake.
        Format: data/bronze/amazon_{tag}_{timestamp}.html
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_tag = tag.replace(" ", "_")
        filename = f"amazon_{safe_tag}_{timestamp}.html"
        
        file_path = self.bronze_path / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        return file_path

if __name__ == "__main__":
    # Smoke Test
    scraper = NexusScraper()
    asyncio.run(scraper.run_extraction())