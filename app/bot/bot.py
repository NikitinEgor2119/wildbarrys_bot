from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from sqlalchemy.future import select
from contextlib import asynccontextmanager
import httpx

from app.db.session import AsyncSessionLocal
from app.db.models import Product, User

bot = Bot(token="7946055764:AAHMJbEO43JWUp3tUDs2HB6wlNj9j4KAiwg")
dp = Dispatcher()


@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


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
            "price": product.get("salePriceU", 0) / 100,  # Цена в рублях
            "rating": product.get("rating", 0),
            "quantity": sum(size.get("qty", 0) for size in product.get("sizes", []))
        }


@dp.message(Command("start"))
async def start(message: types.Message):
    user = message.from_user

    async with get_db() as db:
        result = await db.execute(select(User).where(User.user_id == user.id))
        existing_user = result.scalars().first()

        if existing_user:
            existing_user.username = user.username
            existing_user.first_name = user.first_name
            existing_user.last_name = user.last_name
        else:
            db_user = User(
                user_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            db.add(db_user)

        await db.commit()

    await message.answer("Привет! Введите артикул товара.")


@dp.message()
async def process_artikul(message: types.Message):
    artikul = message.text

    if not artikul.isdigit():
        await message.answer("Артикул должен состоять только из цифр. Попробуйте ещё раз.")
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
                message_text = "Данные товара обновлены!"
            else:
                db_product = Product(
                    name=product_data["name"],
                    artikul=artikul,
                    price=product_data["price"],
                    rating=product_data["rating"],
                    quantity=product_data["quantity"]
                )
                db.add(db_product)
                message_text = "Данные о товаре сохранены!"

            await db.commit()

        await message.answer(
            f"{message_text}\n\n"
            f"Название: {product_data['name']}\n"
            f"Артикул: {artikul}\n"
            f"Цена: {product_data['price']}\n"
            f"Рейтинг: {product_data['rating']}\n"
            f"Количество: {product_data['quantity']}"
        )
    else:
        await message.answer("Товар не найден. Проверьте артикул и попробуйте ещё раз.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
