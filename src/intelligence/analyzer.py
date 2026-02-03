import pandas as pd
from pathlib import Path
from loguru import logger
import time
from datetime import datetime

from src.utils.config_loader import settings
from src.intelligence.gemini_client import GeminiIntelligence

class MarketAnalyzer:
    def __init__(self):
        self.silver_path = Path(settings.paths.silver)
        self.brain = GeminiIntelligence()

    def enrich_products(self):
        # 1. Load the latest Silver file
        files = sorted(self.silver_path.glob("products_*.parquet"))
        if not files:
            logger.error("No Silver data found to analyze!")
            return
        
        latest_file = files[-1]
        logger.info(f"📂 Loading data from: {latest_file.name}")
        df = pd.read_parquet(latest_file)

        # 2. Limit to top 5 for demo (to respect Free Tier limits)
        df_subset = df.head(5).copy()
        
        logger.info("🤖 Starting AI Analysis on top 5 products...")
        
        # 3. Apply AI Analysis
        results = []
        for index, row in df_subset.iterrows():
            analysis = self.brain.analyze_product_appeal(row['title'], row['price'])
            
            # Combine original data with new AI insights
            row_data = row.to_dict()
            row_data['category'] = analysis.get("category")
            row_data['audience'] = ", ".join(analysis.get("target_audience", []))
            row_data['implied_features'] = ", ".join(analysis.get("implied_features", []))
            row_data['value_prop'] = analysis.get("value_proposition")
            
            results.append(row_data)
            
            logger.info("⏳ Waiting 10s to respect API rate limits...")
            time.sleep(10) 

        # 4. Save the Enriched Data (CRITICAL STEP)
        if results:
            enriched_df = pd.DataFrame(results)
            
            # Save as a NEW file so the API picks it up as the "latest"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.silver_path / f"products_enriched_{timestamp}.parquet"
            
            enriched_df.to_parquet(output_file, index=False)
            logger.success(f"💾 Persisted AI Insights to: {output_file.name}")
            
            # Show preview
            print("\n" + "="*50)
            print("🧠 ENRICHED DATA SAVED")
            print(enriched_df[['title', 'value_prop']].head(2).to_string())
            print("="*50)

if __name__ == "__main__":
    analyzer = MarketAnalyzer()
    analyzer.enrich_products()