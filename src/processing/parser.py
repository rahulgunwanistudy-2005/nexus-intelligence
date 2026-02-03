from bs4 import BeautifulSoup, Tag
import pandas as pd
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import List, Optional

from src.utils.config_loader import settings
from src.processing.schemas import ProductSchema

class HtmlParser:
    """
    Refinery Layer: Robustly extracts data using fallback strategies.
    """
    
    def __init__(self):
        self.silver_path = Path(settings.paths.silver)
        self.silver_path.mkdir(parents=True, exist_ok=True)

    def _extract_text(self, item: Tag, selectors: List[str]) -> str:
        """Helper to try multiple CSS selectors."""
        for selector in selectors:
            tag = item.select_one(selector)
            if tag and tag.text.strip():
                return tag.text.strip()
        return ""

    def parse_bronze_file(self, file_path: Path) -> pd.DataFrame:
        logger.info(f"🔨 Parsing Bronze file: {file_path.name}")
        
        with open(file_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "lxml")

        # 1. Identify Product Containers (This part was already working!)
        results = soup.select('div[data-component-type="s-search-result"]')
        logger.info(f"🔍 Found {len(results)} raw items. Extracting details...")

        products = []

        for i, item in enumerate(results):
            try:
                # --- STRATEGY: Fallback Selectors ---
                
                # Title: Try the standard link title, then plain text spans
                title = self._extract_text(item, [
                    "h2 a span", 
                    "span.a-size-medium", 
                    "span.a-size-base-plus", 
                    "h2 span"
                ])

                # Price: Try whole price, then look for nested off-screen text
                price = self._extract_text(item, [
                    "span.a-price-whole", 
                    "span.a-price span.a-offscreen"
                ])

                # Rating: Try the icon alt text
                rating_tag = item.select_one("span.a-icon-alt")
                rating_text = rating_tag.text if rating_tag else "0"
                # Parse "4.5 out of 5 stars" -> 4.5
                try:
                    rating = float(rating_text.split(" ")[0])
                except:
                    rating = 0.0

                # URL: Get the href
                link_tag = item.select_one("h2 a")
                product_url = f"{settings.scraper.base_url}{link_tag['href']}" if link_tag else ""

                # SKIP if critical data is missing (Data Quality Check)
                if not title:
                    # Debug log to see why we are skipping
                    logger.debug(f"⚠️ Item {i}: Missing Title. HTML snippet: {str(item)[:100]}...")
                    continue

                # Validation
                product = ProductSchema(
                    title=title,
                    price=price,
                    rating=rating,
                    product_url=product_url,
                    extracted_at=datetime.now().isoformat()
                )
                
                products.append(product.model_dump())

            except Exception as e:
                logger.warning(f"⚠️ Failed to parse item {i}: {e}")

        # Save to Silver Layer
        if products:
            df = pd.DataFrame(products)
            output_file = self.silver_path / f"products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.parquet"
            df.to_parquet(output_file, index=False)
            logger.success(f"✅ Silver Layer Created: {len(df)} items saved to {output_file.name}")
            
            # Print a sample for verification
            print("\n" + "="*30)
            print("SAMPLE DATA EXTRACTED")
            print("="*30)
            print(df[['title', 'price', 'rating']].head().to_string())
            print("="*30 + "\n")
            
            return df
        else:
            logger.error("❌ No products extracted. The CSS selectors need manual inspection.")
            return pd.DataFrame()

if __name__ == "__main__":
    bronze_dir = Path(settings.paths.bronze)
    # Find the latest HTML file
    latest_file = sorted(bronze_dir.glob("*.html"))[-1]
    
    parser = HtmlParser()
    parser.parse_bronze_file(latest_file)