"""
Nexus Intelligence — Pydantic models
Centralised here so API, tests, and any future services all import from one place.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class Product(BaseModel):
    """A single scraped product."""

    title:      str   = Field(..., min_length=1, description="Full product title")
    price:      float = Field(..., ge=0,         description="Price in INR")
    rating:     float = Field(..., ge=0, le=5,   description="Star rating 0–5")
    url:        str   = Field(default="",        description="Amazon product URL")
    platform:   str   = Field(default="Amazon", description="Source platform")
    scraped_at: str   = Field(...,               description="ISO-8601 timestamp")

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v < 0:
            raise ValueError("price must be >= 0")
        return round(v, 2)

    @field_validator("rating")
    @classmethod
    def rating_in_range(cls, v: float) -> float:
        if not (0 <= v <= 5):
            raise ValueError("rating must be between 0 and 5")
        return round(v, 1)

    @field_validator("url")
    @classmethod
    def ensure_absolute_url(cls, v: str) -> str:
        if v and not v.startswith("http"):
            return f"https://www.amazon.in{v}"
        return v

    @property
    def value_score(self) -> float:
        """rating / price × 10 000 — higher is better value."""
        return round((self.rating / self.price) * 10_000, 2) if self.price > 0 else 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "title":      "Sony WH-1000XM5 Wireless Headphones",
                "price":      29990.0,
                "rating":     4.5,
                "url":        "https://www.amazon.in/dp/B09XSQH1QH",
                "platform":   "Amazon",
                "scraped_at": "2026-02-17T12:00:00",
            }
        }


class ProductResponse(BaseModel):
    """API response envelope for a product search."""

    query:    str          = Field(..., description="The search query")
    count:    int          = Field(..., ge=0, description="Number of results returned")
    products: List[Product] = Field(default_factory=list)
    cached:   bool         = Field(default=False, description="True if served from cache")

    class Config:
        json_schema_extra = {
            "example": {
                "query":    "sony headphones",
                "count":    24,
                "cached":   False,
                "products": [],
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status:    str = Field(default="healthy")
    timestamp: str = Field(..., description="UTC ISO-8601 timestamp")
    version:   str = Field(default="3.0.0")


class ErrorResponse(BaseModel):
    """Standard error envelope."""

    detail:  str           = Field(..., description="Human-readable error message")
    code:    Optional[int] = Field(default=None, description="Internal error code")