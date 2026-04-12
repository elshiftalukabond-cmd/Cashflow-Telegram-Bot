import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, LEADS_CHANNEL_ID
import start
from database import init_db, migrate_db, sync_with_sheets, get_leads_status
from scheduler_manager import scheduler 
from collections import Counter

logging.basicConfig(level=logging.INFO)

async def send_daily_report():
    # Kanalga barcha leadlar ro'yxatini yuborish
    temp_bot = Bot(token=BOT_TOKEN)
    try:
        leads = get_leads_status()
        if not leads: return
        
        step_counts = Counter(step for _, _, step in leads)
        total_leads = len(leads)
        
        report_text = "📊 <b>Umumiy statistika:</b>\n\n"
        report_text += f"👥 Jami botga kirganlar: {total_leads} ta\n\n"
        report_text += "📍 <b>Bosqichlar bo'yicha:</b>\n"
        
        for step, count in sorted(step_counts.items()):
            step_clean = str(step).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            report_text += f"• {step_clean}: {count} ta\n"
            
        if LEADS_CHANNEL_ID:
            # Telegram text limitidan (4096 belgi) oshib ketsa bo'lib yuborish
            # Tag'larni o'rtasidan bo'lmaslik uchun qatorma-qator bo'lamiz
            if len(report_text) > 4000:
                lines = report_text.split('\n')
                current_part = ""
                for line in lines:
                    if len(current_part) + len(line) + 1 > 4000:
                        await temp_bot.send_message(LEADS_CHANNEL_ID, current_part, parse_mode="HTML")
                        current_part = line + '\n'
                    else:
                        current_part += line + '\n'
                if current_part.strip():
                    await temp_bot.send_message(LEADS_CHANNEL_ID, current_part, parse_mode="HTML")
            else:
                await temp_bot.send_message(LEADS_CHANNEL_ID, report_text, parse_mode="HTML")
    except Exception as e:
        logging.error(f"Kanalga hisobot yuborishda xato: {e}")
    finally:
        await temp_bot.session.close()

async def main():
    init_db()
    migrate_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start.router)

    if not scheduler.running:
        scheduler.start()

    from database import recover_unsynced_users_from_sheet
    print("Tiklash va sinxronizatsiya tekshiruvi boshlanmoqda...")
    asyncio.create_task(recover_unsynced_users_from_sheet())
    
    # Namuna tarzida bot yonganda darhol 1 marta hisobot yuboramiz
    print("Namuna hisobot yuborilmoqda...")
    asyncio.create_task(send_daily_report())

    # Google sheets bilan ishlashni orqaga qaytarish, har 10 daqiqada sinxronizatsiya qiladi.
    scheduler.add_job(
        sync_with_sheets, 
        'interval', 
        minutes=10, 
        id='sync_report_job', 
        replace_existing=True
    )

    # 12:00 va 23:50 da yuboriladigan cron tasklar
    scheduler.add_job(
        send_daily_report, 
        'cron', 
        hour=12, 
        minute=0, 
        id='daily_report_12', 
        replace_existing=True
    )

    scheduler.add_job(
        send_daily_report, 
        'cron', 
        hour=23, 
        minute=50, 
        id='daily_report_2350', 
        replace_existing=True
    )

    print("Target bot ishga tushdi...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot to'xtatildi.")