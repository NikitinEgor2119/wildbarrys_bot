import asyncio
import logging
from fastapi import FastAPI, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from aiogram import Bot, Dispatcher
from app.db.session import get_db
from app.bot.handlers import register_handlers
from app.api.v1.endpoints.products import router as products_router


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


DATABASE_URL = "postgresql+asyncpg://user:user@45.91.201.247:5432/mydatabase"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


BOT_TOKEN = "7946055764:AAHMJbEO43JWUp3tUDs2HB6wlNj9j4KAiwg"
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


app = FastAPI()
app.include_router(products_router)


scheduler = AsyncIOScheduler()


register_handlers(dp)


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