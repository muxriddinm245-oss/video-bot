import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
import database as db
from handlers import user, admin, payment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)


async def start_bot():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(admin.router)
    dp.include_router(payment.router)
    dp.include_router(user.router)

    await db.init_db()
    logging.info("✅ Database tayyor")
    logging.info("🚀 Bot ishga tushdi!")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


async def main():
    # Auto-restart: internet uzilsa yoki xato bo'lsa — qayta ulanadi
    while True:
        try:
            await start_bot()
        except Exception as e:
            logging.error(f"❌ Xato yuz berdi: {e}")
            logging.info("🔄 5 soniyadan keyin qayta ulanadi...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
