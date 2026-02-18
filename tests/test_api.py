"""Tests for the FastAPI endpoints."""
import pytest
import pandas as pd
from pathlib import Path
from unittest.mock import patch

# conftest.py already adds project root to sys.path
# _boot_clear runs at import time — data dirs are pre-created by conftest.py
from src.api.main import app
from fastapi.testclient import TestClient

client = TestClient(app)


# Health and root endpoints

def test_health_returns_200():
    r = client.get("/health")
    assert r.status_code == 200

def test_health_body():
    data = client.get("/health").json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    assert data["version"] == "3.0.0"

def test_root_returns_version():
    data = client.get("/").json()
    assert data["version"] == "3.0.0"


# Products endpoint validation

def test_products_missing_query_is_422():
    assert client.get("/api/products").status_code == 422

def test_products_query_too_short_is_422():
    assert client.get("/api/products?query=a").status_code == 422

def test_products_invalid_limit_is_422():
    assert client.get("/api/products?query=test&limit=0").status_code == 422

def test_products_invalid_rating_is_422():
    assert client.get("/api/products?query=test&min_rating=6").status_code == 422


# Products endpoint behavior

def _make_parquet(tmp_path: Path, rows: list) -> Path:
    df = pd.DataFrame(rows)
    p = tmp_path / "test.parquet"
    df.to_parquet(p)
    return p


@patch("src.api.main.get_cached_file")
@patch("src.api.main.run_pipeline")
def test_products_fresh_data(mock_pipeline, mock_cache, tmp_path):
    pq = _make_parquet(tmp_path, [{
        "title": "Sony WH-1000XM5",
        "price": 29990.0, "rating": 4.5,
        "url": "https://amazon.in/dp/test",
        "platform": "Amazon",
        "scraped_at": "2026-01-01T00:00:00",
    }])
    mock_cache.return_value = None
    mock_pipeline.return_value = pq

    r = client.get("/api/products?query=headphones&limit=10")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["cached"] is False
    assert data["products"][0]["title"] == "Sony WH-1000XM5"


@patch("src.api.main.get_cached_file")
def test_products_cached_data(mock_cache, tmp_path):
    pq = _make_parquet(tmp_path, [{
        "title": "Cached Headphone",
        "price": 999.0, "rating": 4.0,
        "url": "", "platform": "Amazon",
        "scraped_at": "2026-01-01T00:00:00",
    }])
    mock_cache.return_value = pq

    r = client.get("/api/products?query=headphones&limit=5")
    assert r.status_code == 200
    assert r.json()["cached"] is True


@patch("src.api.main.get_cached_file")
@patch("src.api.main.run_pipeline")
def test_rating_filter_applied(mock_pipeline, mock_cache, tmp_path):
    pq = _make_parquet(tmp_path, [
        {"title": "Good one",  "price": 1000.0, "rating": 4.5, "url": "", "platform": "Amazon", "scraped_at": "2026-01-01T00:00:00"},
        {"title": "Bad one",   "price": 500.0,  "rating": 2.0, "url": "", "platform": "Amazon", "scraped_at": "2026-01-01T00:00:00"},
    ])
    mock_cache.return_value = None
    mock_pipeline.return_value = pq

    r = client.get("/api/products?query=test&min_rating=4.0")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 1
    assert data["products"][0]["title"] == "Good one"


@patch("src.api.main.get_cached_file")
@patch("src.api.main.run_pipeline")
def test_limit_applied(mock_pipeline, mock_cache, tmp_path):
    rows = [{"title": f"Product {i}", "price": float(100*i), "rating": 4.0,
             "url": "", "platform": "Amazon", "scraped_at": "2026-01-01T00:00:00"}
            for i in range(1, 11)]
    pq = _make_parquet(tmp_path, rows)
    mock_cache.return_value = None
    mock_pipeline.return_value = pq

    r = client.get("/api/products?query=test&limit=3")
    assert r.status_code == 200
    assert r.json()["count"] == 3