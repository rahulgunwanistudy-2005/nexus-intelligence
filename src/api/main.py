from fastapi import FastAPI, HTTPException
import pandas as pd
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

# --- NEW IMPORTS ---
from src.utils.config_loader import settings
from src.ingestion.scraper import NexusScraper
from src.processing.parser import HtmlParser
from src.intelligence.gemini_client import GeminiIntelligence

app = FastAPI(
    title="Nexus Intelligence API",
    description="Industry-grade Market Analysis Engine",
    version="1.0.0"
)

# Global cache
DATA_CACHE = None

class ProductResponse(BaseModel):
    title: str
    price: float
    rating: float
    audience: Optional[str] = "Pending Analysis"  # Default value
    value_prop: Optional[str] = "Pending Analysis" # Default value

def load_all_data():
    """Loads ALL parquet files from the silver directory."""
    silver_path = Path(settings.paths.silver)
    files = sorted(silver_path.glob("*.parquet"))
    
    if not files:
        return pd.DataFrame()
    
    # Read all files and combine them
    dfs = [pd.read_parquet(f) for f in files]
    combined_df = pd.concat(dfs, ignore_index=True)
    
    # Deduplicate based on Title
    return combined_df.drop_duplicates(subset=['title'])

@app.on_event("startup")
def startup_event():
    global DATA_CACHE
    DATA_CACHE = load_all_data()
    print(f"✅ Loaded {len(DATA_CACHE)} total products into memory.")

@app.get("/products/search", response_model=List[ProductResponse])
def search_products(query: str, min_rating: float = 0.0):
    if DATA_CACHE is None or DATA_CACHE.empty:
        return []

    # Case-insensitive search
    mask = (
        DATA_CACHE['title'].str.contains(query, case=False, na=False) & 
        (DATA_CACHE['rating'] >= min_rating)
    )
    results = DATA_CACHE[mask].head(20)
    
    # Fill NaN values for cleaner JSON response
    results = results.fillna("Pending Analysis")
    
    return results.to_dict(orient="records")

# --- NEW ENDPOINT: LIVE INGESTION ---
@app.post("/ingest/live")
async def trigger_live_ingestion(search_term: str):
    """
    Triggers a live scrape -> parse cycle for a new term.
    """
    try:
        print(f"🚀 Triggering Live Ingestion for: {search_term}")
        
        # 1. Run Scraper (Bronze)
        scraper = NexusScraper()
        raw_file_path = await scraper.run_extraction(query=search_term)
        
        # 2. Run Parser (Silver)
        parser = HtmlParser()
        new_df = parser.parse_bronze_file(raw_file_path)
        
        if new_df.empty:
            raise HTTPException(status_code=404, detail="Scraper found no products.")

        # 3. Update Global Cache (Hot Reload)
        global DATA_CACHE
        if DATA_CACHE is None:
            DATA_CACHE = new_df
        else:
            DATA_CACHE = pd.concat([new_df, DATA_CACHE], ignore_index=True)
            DATA_CACHE.drop_duplicates(subset=['title'], inplace=True)
            
        return {
            "status": "success", 
            "message": f"Successfully ingested {len(new_df)} products for '{search_term}'",
            "count": len(new_df)
        }

    except Exception as e:
        print(f"❌ Ingestion Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))