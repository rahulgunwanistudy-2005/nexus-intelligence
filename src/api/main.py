"""
Nexus Intelligence API  —  v3.0
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta
import subprocess, os, sys

sys.path.insert(0, "/app")
from src.api.models import Product, ProductResponse, HealthResponse

def _boot_clear() -> None:
    deleted = 0
    for d in [Path("data/raw"), Path("data/processed")]:
        d.mkdir(parents=True, exist_ok=True)
        for f in d.glob("*"):
            if f.is_file() and f.suffix in (".html", ".parquet"):
                f.unlink(); deleted += 1
    print(f"[CACHE] Boot: cleared {deleted} cached file(s)")
_boot_clear()

MAX_PAGES  = int(os.getenv("MAX_PAGES", "3"))
CACHE_TTL  = int(os.getenv("CACHE_TTL_HOURS", "24"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"[START] Nexus API v3.0  MAX_PAGES={MAX_PAGES}  CACHE_TTL={CACHE_TTL}h")
    yield
    print("👋 Nexus API shutting down")

app = FastAPI(title="Nexus Intelligence API", version="3.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

def query_to_key(q: str) -> str:
    return q.lower().strip().replace(" ", "_")

def clear_all_cache() -> int:
    deleted = 0
    for d in [Path("data/raw"), Path("data/processed")]:
        if d.exists():
            for f in d.glob("*"):
                if f.is_file() and f.suffix in (".html", ".parquet"):
                    f.unlink(); deleted += 1
    if deleted: print(f"[CACHE] Cleared {deleted} file(s)")
    return deleted

def get_cached_file(query: str) -> Optional[Path]:
    key = query_to_key(query)
    matches = list(Path("data/processed").glob(f"{key}_*.parquet"))
    if not matches: return None
    latest = max(matches, key=lambda f: f.stat().st_mtime)
    if datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime) > timedelta(hours=CACHE_TTL):
        return None
    print(f"[OK] Cache hit: {latest.name}"); return latest

def run_pipeline(query: str) -> Path:
    key = query_to_key(query)
    clear_all_cache()
    env = {**os.environ, "SEARCH_TERM": query, "MAX_PAGES": str(MAX_PAGES)}

    r = subprocess.run(["python", "-m", "src.scraper.amazon"],
        env=env, capture_output=True, text=True, timeout=120, cwd="/app")
    print(r.stdout)
    if r.returncode != 0:
        raise HTTPException(500, detail=f"Scraper failed: {r.stderr[:300]}")

    html_files = sorted(Path("data/raw").glob("*.html"), key=lambda f: f.stat().st_mtime)
    if not html_files: raise HTTPException(500, detail="No HTML file produced")
    latest_html = html_files[-1]

    r = subprocess.run(["python", "-m", "src.parser.html_parser"],
        env={**env, "INPUT_FILE": str(latest_html), "OUTPUT_KEY": key},
        capture_output=True, text=True, timeout=60, cwd="/app")
    print(r.stdout)
    if r.returncode != 0:
        raise HTTPException(500, detail=f"Parser failed: {r.stderr[:300]}")

    pq = sorted(Path("data/processed").glob(f"{key}_*.parquet"), key=lambda f: f.stat().st_mtime)
    if not pq:
        pq = sorted(Path("data/processed").glob("*.parquet"), key=lambda f: f.stat().st_mtime)
    if not pq: raise HTTPException(500, detail="No parquet file produced")
    return pq[-1]

@app.get("/", include_in_schema=False)
def root(): return {"name": "Nexus Intelligence API", "version": "3.0.0"}

@app.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="healthy", timestamp=datetime.utcnow().isoformat(), version="3.0.0")

@app.get("/api/products", response_model=ProductResponse)
def get_products(
    query:      str   = Query(..., min_length=2),
    limit:      int   = Query(20, ge=1, le=100),
    min_rating: float = Query(0.0, ge=0.0, le=5.0),
):
    print(f"\n{'='*50}\n[REQUEST] query='{query}' limit={limit} min_rating={min_rating}")
    cached = False
    cf = get_cached_file(query)
    if cf:
        df = pd.read_parquet(cf); cached = True
    else:
        try: pq = run_pipeline(query)
        except subprocess.TimeoutExpired:
            raise HTTPException(504, detail="Timed out — please try again")
        df = pd.read_parquet(pq)
    if min_rating > 0: df = df[df["rating"] >= min_rating]
    df = df.head(limit).reset_index(drop=True)
    return ProductResponse(query=query, count=len(df),
                           products=df.to_dict("records"), cached=cached)