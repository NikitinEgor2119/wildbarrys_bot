from aiogram import types
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models import User, Product
from app.services.wildberries import fetch_product_data

async def start(message: types.Message, db: AsyncSession):
    try:
        user = message.from_user
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
    except Exception as e:
        await message.answer("Произошла ошибка. Попробуйте позже.")
        print(f"Error in start handler: {e}")

async def process_artikul(message: types.Message, db: AsyncSession):
    try:
        artikul = message.text
        if not artikul.isdigit():
            await message.answer("Артикул должен быть числом. Попробуйте снова.")
            return

        artikul = int(artikul)
        product_data = await fetch_product_data(artikul)

        if product_data:
            existing_product = await db.execute(
                select(Product).where(Product.artikul == artikul)
            )
            existing_product = existing_product.scalars().first()

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
    except Exception as e:
        await message.answer("Произошла ошибка. Попробуйте позже.")
        print(f"Error in process_artikul handler: {e}")

def register_handlers(dp):
    dp.message.register(start, Command("start"))
    dp.message.register(process_artikul)