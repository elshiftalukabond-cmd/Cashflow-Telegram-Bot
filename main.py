import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, LEADS_CHANNEL_ID
import start
from database import init_db, migrate_db, sync_with_sheets, get_leads_status
from scheduler_manager import scheduler 

logging.basicConfig(level=logging.INFO)

# YANGI: Ham sheetga, ham kanalga yuboradigan umumiy funksiya
async def sync_and_report():
    # 1. Sheetsga ma'lumotlarni yozish (asl funksiya o'zgarmaydi)
    await sync_with_sheets()
    
    # 2. Kanalga barcha leadlar ro'yxatini yuborish
    temp_bot = Bot(token=BOT_TOKEN)
    try:
        leads = get_leads_status()
        if not leads: return
        
        report_text = "📍 <b>Leadlar joylashgan bosqichlar ro'yxati:</b>\n\n"
        for u_id, uname, step in leads:
            name_clean = uname.replace('<', '').replace('>', '') if uname else f"ID:{u_id}"
            if name_clean == "Noma'lum" or not name_clean.strip():
                name_clean = f"Mijoz {u_id}"
                
            link = f'<a href="tg://user?id={u_id}">{name_clean}</a>'
            report_text += f"• {link} — <i>{step}</i>\n"
            
        if LEADS_CHANNEL_ID:
            # Telegram text limitidan (4096 belgi) oshib ketsa bo'lib yuborish
            if len(report_text) > 4000:
                parts = [report_text[i:i+4000] for i in range(0, len(report_text), 4000)]
                for part in parts:
                    await temp_bot.send_message(LEADS_CHANNEL_ID, part, parse_mode="HTML")
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

    # O'ZGARISH: Endi faqat sync_with_sheets emas, balki sync_and_report ishlaydi
    scheduler.add_job(
        sync_and_report, 
        'interval', 
        minutes=10, 
        id='sync_report_job', 
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