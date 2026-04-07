import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
import start
from database import init_db, migrate_db, sync_with_sheets
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

logging.basicConfig(level=logging.INFO)

os.makedirs("data", exist_ok=True)
# Vazifalarni faylda saqlash (Restartdan himoya - Volume)
jobstores = {'default': SQLAlchemyJobStore(url='sqlite:///data/jobs.sqlite')}
scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Asia/Tashkent")

async def main():
    init_db()
    migrate_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start.router)

    # 1. Avval schedulerni ishga tushiramiz
    scheduler.start()

    # 2. Keyin vazifani qo'shamiz (replace_existing=True xatolikni oldini oladi)
    scheduler.add_job(
        sync_with_sheets, 
        'interval', 
        minutes=10, 
        id='sync_job', 
        replace_existing=True
    )

    print("Target uchun tayyor bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    # Scheduler'ni barcha handlerlarga yetib borishi uchun uzatamiz
    await dp.start_polling(bot, scheduler=scheduler)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")