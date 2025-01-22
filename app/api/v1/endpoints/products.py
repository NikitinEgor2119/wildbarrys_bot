from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Product
from app.db.session import get_db
import httpx
from pydantic import BaseModel

router = APIRouter()


class ProductRequest(BaseModel):
    artikul: int


async def fetch_product_data(artikul: int):
    url = f"https://card.wb.ru/cards/v1/detail?appType=1&curr=rub&dest=-1257786&spp=30&nm={artikul}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
        product_data = data.get("data", {}).get("products", [])
        if not product_data:
            return None
        product = product_data[0]
        return {
            "name": product.get("name"),
            "artikul": artikul,
            "price": product.get("salePriceU", 0) / 100,
            "rating": product.get("rating", 0),
            "quantity": sum(size.get("qty", 0) for size in product.get("sizes", []))
        }


@router.post("/api/v1/products")
async def create_product(product: ProductRequest, db: AsyncSession = Depends(get_db)):
    product_data = await fetch_product_data(product.artikul)
    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")

    db_product = Product(**product_data)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return {"message": "Product data saved successfully!"}
