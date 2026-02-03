from pydantic import BaseModel, HttpUrl, validator
from typing import Optional

class ProductSchema(BaseModel):
    """
    Silver Layer Schema.
    Defines exactly what a valid product looks like in our system.
    """
    title: str
    price: float
    rating: Optional[float] = None
    reviews_count: int = 0
    product_url: str  # Kept as str to avoid strict HttpUrl validation issues with relative paths
    extracted_at: str

    @validator('title')
    def clean_title(cls, v):
        return v.strip()

    @validator('price', pre=True)
    def clean_price(cls, v):
        """Removes currency symbols and commas."""
        if isinstance(v, (float, int)):
            return v
        if not v:
            return 0.0
        # Remove '₹', ',', and whitespace
        clean = v.replace('₹', '').replace(',', '').strip()
        try:
            return float(clean)
        except ValueError:
            return 0.0