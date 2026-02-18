"""
Amazon Product Scraper - Production Grade
Scrapes product listings from Amazon India with anti-detection measures.
"""

import os
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, Page, Browser


class AmazonScraper:
    """Production-grade Amazon scraper with anti-bot measures."""
    
    def __init__(
        self,
        headless: bool = True,
        max_pages: int = 4,
        timeout: int = 60000
    ):
        """
        Initialize scraper.
        
        Args:
            headless: Run browser in headless mode
            max_pages: Maximum pages to scrape
            timeout: Navigation timeout in milliseconds
        """
        self.headless = headless
        self.max_pages = max_pages
        self.timeout = timeout
        self.output_dir = Path("data/raw")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def scrape(self, search_term: str) -> Dict[str, Any]:
        """
        Scrape Amazon for given search term.
        
        Args:
            search_term: Product to search for
            
        Returns:
            Dict with status, filename, and metadata
        """
        print(f"[SCAN] Scraping Amazon for: '{search_term}'")
        
        with sync_playwright() as playwright:
            browser = self._launch_browser(playwright)
            page = browser.new_page()
            
            try:
                # Configure page
                self._configure_page(page)
                
                # Scrape multiple pages
                all_html = []
                total_products = 0
                
                for page_num in range(1, self.max_pages + 1):
                    print(f"\n[PAGE] Page {page_num}/{self.max_pages}")
                    
                    html, product_count = self._scrape_page(
                        page, search_term, page_num
                    )
                    
                    if html and product_count > 0:
                        all_html.append(html)
                        total_products += product_count
                        
                        # Human-like delay between pages
                        if page_num < self.max_pages:
                            delay = random.uniform(2.0, 4.0)
                            print(f"[WAIT] Waiting {delay:.1f}s...")
                            time.sleep(delay)
                    else:
                        print("[WARN] No more results")
                        break
                
                # Save combined HTML
                if all_html:
                    filename = self._save_html(search_term, all_html)
                    
                    return {
                        "success": True,
                        "filename": str(filename),
                        "products": total_products,
                        "pages": len(all_html)
                    }
                else:
                    return {
                        "success": False,
                        "error": "No data collected"
                    }
                    
            except Exception as e:
                print(f"[ERROR] Error: {e}")
                return {
                    "success": False,
                    "error": str(e)
                }
            finally:
                browser.close()
    
    def _launch_browser(self, playwright) -> Browser:
        """Launch browser with anti-detection settings."""
        return playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
            ]
        )
    
    def _configure_page(self, page: Page) -> None:
        """Configure page with realistic settings."""
        # Set viewport
        page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Remove automation flags
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
    
    def _scrape_page(
        self, 
        page: Page, 
        search_term: str, 
        page_num: int
    ) -> tuple[Optional[str], int]:
        """
        Scrape a single page.
        
        Returns:
            Tuple of (html_content, product_count)
        """
        # Build URL
        clean_term = search_term.replace(" ", "+")
        url = f"https://www.amazon.in/s?k={clean_term}&page={page_num}"
        
        try:
            # Navigate
            page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            time.sleep(random.uniform(1.5, 2.5))
            
            # Wait for results
            page.wait_for_selector("div.s-main-slot", timeout=10000)
            
            # Scroll to load lazy content
            self._scroll_page(page)
            
            # Count products
            product_count = page.locator(
                "div[data-component-type='s-search-result']"
            ).count()
            
            print(f"[OK] Found {product_count} products")
            
            if product_count == 0:
                return None, 0
            
            return page.content(), product_count
            
        except Exception as e:
            print(f"[WARN] Page {page_num} failed: {e}")
            return None, 0
    
    def _scroll_page(self, page: Page) -> None:
        """Scroll page to trigger lazy loading."""
        for _ in range(5):
            page.evaluate("window.scrollBy(0, window.innerHeight)")
            time.sleep(random.uniform(0.5, 1.0))
        
        # Scroll to bottom
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1)
    
    def _save_html(self, search_term: str, html_pages: list[str]) -> Path:
        """Save HTML to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        clean_term = search_term.replace(" ", "_")
        filename = self.output_dir / f"amazon_{clean_term}_{timestamp}.html"
        
        # Combine pages
        combined = "\n<!-- PAGE BREAK -->\n".join(html_pages)
        
        filename.write_text(combined, encoding="utf-8")
        
        size_kb = filename.stat().st_size / 1024
        print(f"\n[SAVED] Saved: {filename.name} ({size_kb:.1f} KB)")
        
        return filename


def main():
    """CLI entry point for testing."""
    search_term = os.getenv("SEARCH_TERM", "headphones")
    max_pages = int(os.getenv("MAX_PAGES", "3"))
    
    scraper = AmazonScraper(max_pages=max_pages)
    result = scraper.scrape(search_term)
    
    if result["success"]:
        print(f"\n[OK] Success! Scraped {result['products']} products")
    else:
        print(f"\n[ERROR] Failed: {result.get('error')}")
        exit(1)


if __name__ == "__main__":
    main()