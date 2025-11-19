import os
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import db, create_document, get_documents

app = FastAPI(title="Product Compare API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ProductIn(BaseModel):
    title: str
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    rating: float = Field(0, ge=0, le=5)
    category: str
    brand: Optional[str] = None
    image_url: Optional[str] = None
    url: Optional[str] = None
    in_stock: bool = True


@app.get("/")
def read_root():
    return {"message": "Hello from FastAPI Backend!"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"

    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    import os as _os
    response["database_url"] = "✅ Set" if _os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if _os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response


# -------- Product Comparison Endpoints -------- #

@app.post("/api/products/seed")
def seed_products():
    """Seed database with sample products for demo."""
    if db is None:
        return {"ok": False, "error": "Database not configured"}

    samples = [
        {
            "title": "ApexCard Pro X",
            "description": "Premium smart card with NFC and biometric auth",
            "price": 299.0,
            "rating": 4.7,
            "category": "Fintech",
            "brand": "Apex",
            "image_url": "https://images.unsplash.com/photo-1607082350899-7e105aa886ae?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/apex-pro-x",
            "in_stock": True,
        },
        {
            "title": "NovaPay Lite",
            "description": "Lightweight contactless payment card",
            "price": 129.0,
            "rating": 4.3,
            "category": "Fintech",
            "brand": "Nova",
            "image_url": "https://images.unsplash.com/photo-1556740724-df2eab7442f8?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/novapay-lite",
            "in_stock": True,
        },
        {
            "title": "Glacier Card",
            "description": "Glass-morphic premium metal card",
            "price": 199.0,
            "rating": 4.5,
            "category": "Fintech",
            "brand": "Glacier",
            "image_url": "https://images.unsplash.com/photo-1563013544-824ae1b704d3?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/glacier",
            "in_stock": True,
        },
        {
            "title": "VoltCharge Mini",
            "description": "Compact USB-C fast charger",
            "price": 29.0,
            "rating": 4.6,
            "category": "Accessories",
            "brand": "Volt",
            "image_url": "https://images.unsplash.com/photo-1586816001966-79b736744398?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/volt-mini",
            "in_stock": True,
        },
        {
            "title": "VoltCharge Max",
            "description": "65W GaN fast charger",
            "price": 49.0,
            "rating": 4.4,
            "category": "Accessories",
            "brand": "Volt",
            "image_url": "https://images.unsplash.com/photo-1609592424311-7972ea278e82?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/volt-max",
            "in_stock": True,
        },
        {
            "title": "Aurora Buds",
            "description": "Wireless earbuds with ANC",
            "price": 89.0,
            "rating": 4.2,
            "category": "Audio",
            "brand": "Aurora",
            "image_url": "https://images.unsplash.com/photo-1518447954390-75f0b42b9d1c?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/aurora-buds",
            "in_stock": True,
        },
        {
            "title": "Aurora Buds Pro",
            "description": "Premium earbuds with spatial audio",
            "price": 149.0,
            "rating": 4.6,
            "category": "Audio",
            "brand": "Aurora",
            "image_url": "https://images.unsplash.com/photo-1590658268037-6bf12165a8df?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/aurora-buds-pro",
            "in_stock": True,
        },
        {
            "title": "Nimbus Wallet",
            "description": "Minimalist RFID-blocking wallet",
            "price": 39.0,
            "rating": 4.1,
            "category": "Lifestyle",
            "brand": "Nimbus",
            "image_url": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c?q=80&w=1200&auto=format&fit=crop",
            "url": "https://example.com/nimbus-wallet",
            "in_stock": True,
        },
    ]

    inserted = 0
    for s in samples:
        try:
            create_document("product", s)
            inserted += 1
        except Exception:
            pass

    return {"ok": True, "inserted": inserted}


def compute_best_value(products: List[dict]) -> List[dict]:
    if not products:
        return products
    prices = sorted([p.get("price", 0) for p in products])
    mid = len(prices) // 2
    median = (prices[mid] if len(prices) % 2 == 1 else (prices[mid - 1] + prices[mid]) / 2) or 0
    p25 = prices[max(0, len(prices) // 4 - 1)] if prices else 0

    result = []
    for p in products:
        price = p.get("price", 0)
        rating = p.get("rating", 0)
        is_best = rating >= 4.3 and price <= max(p25, 0.75 * median)
        q = p.copy()
        q["is_best_value"] = bool(is_best)
        result.append(q)
    return result


@app.get("/api/products/recommended")
def get_recommended(limit: int = 8):
    if db is None:
        return {"ok": False, "error": "Database not configured"}
    items = get_documents("product", {})
    # Sort: high rating then low price
    items.sort(key=lambda x: (-float(x.get("rating", 0)), float(x.get("price", 1e9))))
    items = items[:limit]
    items = compute_best_value(items)
    return {"ok": True, "items": items}


@app.get("/api/products/search")
def search_products(
    q: Optional[str] = Query(None, description="search term"),
    category: Optional[str] = None,
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    sort: Optional[str] = Query("relevance", description="relevance|price_asc|price_desc|rating_desc"),
    limit: int = 50,
):
    if db is None:
        return {"ok": False, "error": "Database not configured"}

    # Build filter
    filter_dict: dict = {}
    if q:
        # Simple regex search in title/description/brand
        filter_dict["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"brand": {"$regex": q, "$options": "i"}},
        ]
    if category:
        filter_dict["category"] = category
    if min_price is not None or max_price is not None:
        price_filter = {}
        if min_price is not None:
            price_filter["$gte"] = min_price
        if max_price is not None:
            price_filter["$lte"] = max_price
        filter_dict["price"] = price_filter
    if min_rating is not None:
        filter_dict["rating"] = {"$gte": min_rating}

    items = get_documents("product", filter_dict)

    # Sorting
    if sort == "price_asc":
        items.sort(key=lambda x: float(x.get("price", 0)))
    elif sort == "price_desc":
        items.sort(key=lambda x: -float(x.get("price", 0)))
    elif sort == "rating_desc":
        items.sort(key=lambda x: -float(x.get("rating", 0)))
    else:  # relevance: prefer items that matched q with higher rating and lower price
        items.sort(key=lambda x: (-float(x.get("rating", 0)), float(x.get("price", 1e9))))

    items = items[:limit]
    items = compute_best_value(items)

    # Collect categories present
    categories = sorted(list({i.get("category", "Other") for i in items}))

    return {"ok": True, "count": len(items), "items": items, "categories": categories}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
