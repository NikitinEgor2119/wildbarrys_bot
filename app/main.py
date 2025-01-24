import asyncio
import logging
from fastapi import FastAPI, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


DATABASE_URL = "postgresql+asyncpg://user:user@localhost/dbname"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

BOT_TOKEN = "7946055764:AAHMJbEO43JWUp3tUDs2HB6wlNj9j4KAiwg"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


app = FastAPI()


scheduler = AsyncIOScheduler()


from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True)
    username = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    artikul = Column(Integer, unique=True, index=True)
    price = Column(Float)
    rating = Column(Float)
    quantity = Column(Integer)


@dp.message(Command("start"))
async def start(message: types.Message):
    try:
        user = message.from_user
        db = await anext(get_db())
        logger.debug("Database session acquired")


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
            logger.debug("New user added to the database")

        await message.answer("Привет! Введите артикул товара.")
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
    finally:
        await db.close()

@dp.message()
async def process_artikul(message: types.Message):
    try:
        artikul = message.text
        if not artikul.isdigit():
            await message.answer("Артикул должен быть числом. Попробуйте снова.")
            return

        artikul = int(artikul)
        db = await anext(get_db())
        logger.debug("Database session acquired")


        async def fetch_product_data(artikul: int):
            return {
                "name": "Пример товара",
                "price": 100.0,
                "rating": 4.5,
                "quantity": 10
            }

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
            logger.debug("Product data updated in the database")

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
        logger.error(f"Error in process_artikul handler: {e}")
    finally:
        await db.close()


@app.get("/api/v1/subscribe/{artikul}")
async def subscribe_product(artikul: int, db: AsyncSession = Depends(get_db)):
    scheduler.add_job(periodic_fetch, 'interval', minutes=30, args=(artikul, db))
    scheduler.start()
    return {"message": f"Subscribed to product {artikul}"}

async def periodic_fetch(artikul: int, db: AsyncSession):
    try:
        async def fetch_product_data(artikul: int):
            return {
                "name": "Пример товара",
                "price": 100.0,
                "rating": 4.5,
                "quantity": 10
            }

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
            logger.debug("Product data updated in the database")
    except Exception as e:
        logger.error(f"Error in periodic_fetch: {e}")


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