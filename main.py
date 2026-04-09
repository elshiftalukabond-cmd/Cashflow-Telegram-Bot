import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
import start
from database import init_db, migrate_db, sync_with_sheets

# --- Markazlashgan schedulerni chaqiramiz ---
from scheduler_manager import scheduler 

logging.basicConfig(level=logging.INFO)

async def main():
    init_db()
    migrate_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start.router)

    # 1. Schedulerni ishga tushiramiz
    scheduler.start()

    # 2. Sheets bilan sinxronizatsiya
    scheduler.add_job(
        sync_with_sheets, 
        'interval', 
        minutes=10, 
        id='sync_job', 
        replace_existing=True
    )

    print("Target bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    # E'tibor bering: scheduler parametrini bu yerdan olib tashladik
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")