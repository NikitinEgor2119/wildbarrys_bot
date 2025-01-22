from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.db.session import get_db
from app.db.models import Product
from app.api.v1.endpoints.products import router as products_router, fetch_product_data

scheduler = AsyncIOScheduler()

app = FastAPI()

# Подключаем маршруты из products.py
app.include_router(products_router)

async def periodic_fetch(artikul: int, db: AsyncSession):
    product_data = await fetch_product_data(artikul)
    if product_data:
        db_product = Product(**product_data)
        db.add(db_product)
        await db.commit()

@app.get("/api/v1/subscribe/{artikul}")
async def subscribe_product(artikul: int, db: AsyncSession = Depends(get_db)):
    scheduler.add_job(periodic_fetch, 'interval', minutes=30, args=(artikul, db))
    scheduler.start()
    return {"message": f"Subscribed to product {artikul}"}

