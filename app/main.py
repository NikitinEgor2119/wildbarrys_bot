import asyncio
from fastapi import FastAPI, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession
from aiogram import Bot, Dispatcher, executor, types
from aiogram.filters import Command

from app.db.session import get_db
from app.db.models import Product, User
from app.api.v1.endpoints.products import fetch_product_data


BOT_TOKEN = "7946055764:AAHMJbEO43JWUp3tUDs2HB6wlNj9j4KAiwg"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)


app = FastAPI()


scheduler = AsyncIOScheduler()


@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user
    async with get_db() as db:
        existing_user = await db.execute(
            select(User).where(User.user_id == user.id)
        )
        if not existing_user.scalars().first():
            db.add(User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            ))
            await db.commit()
    await message.answer("Привет! Введите артикул товара.")

@dp.message()
async def process_artikul(message: types.Message):
    artikul = message.text
    if not artikul.isdigit():
        await message.answer("Артикул должен быть числом. Попробуйте снова.")
        return

    artikul = int(artikul)
    product_data = await fetch_product_data(artikul)

    if product_data:
        async with get_db() as db:
            result = await db.execute(select(Product).where(Product.artikul == artikul))
            existing_product = result.scalars().first()
            if existing_product:
                existing_product.name = product_data["name"]
                existing_product.price = product_data["price"]
                existing_product.rating = product_data["rating"]
                existing_product.quantity = product_data["quantity"]
            else:
                db.add(Product(
                    name=product_data["name"],
                    artikul=artikul,
                    price=product_data["price"],
                    rating=product_data["rating"],
                    quantity=product_data["quantity"]
                ))
            await db.commit()

        await message.answer(
            f"Название: {product_data['name']}\n"
            f"Артикул: {artikul}\n"
            f"Цена: {product_data['price']}\n"
            f"Рейтинг: {product_data['rating']}\n"
            f"Количество: {product_data['quantity']}"
        )
    else:
        await message.answer("Товар не найден. Проверьте артикул.")


@app.get("/api/v1/subscribe/{artikul}")
async def subscribe_product(artikul: int, db: AsyncSession = Depends(get_db)):
    scheduler.add_job(periodic_fetch, 'interval', minutes=30, args=(artikul, db))
    scheduler.start()
    return {"message": f"Subscribed to product {artikul}"}

async def periodic_fetch(artikul: int, db: AsyncSession):
    product_data = await fetch_product_data(artikul)
    if product_data:
        async with db.begin():
            result = await db.execute(select(Product).where(Product.artikul == artikul))
            existing_product = result.scalars().first()
            if existing_product:
                existing_product.name = product_data["name"]
                existing_product.price = product_data["price"]
                existing_product.rating = product_data["rating"]
                existing_product.quantity = product_data["quantity"]
            else:
                db.add(Product(
                    name=product_data["name"],
                    artikul=artikul,
                    price=product_data["price"],
                    rating=product_data["rating"],
                    quantity=product_data["quantity"]
                ))


async def main():
    bot_task = asyncio.create_task(dp.start_polling(bot))
    uvicorn_task = asyncio.create_task(run_uvicorn())
    await asyncio.gather(bot_task, uvicorn_task)

async def run_uvicorn():
    import uvicorn
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())


