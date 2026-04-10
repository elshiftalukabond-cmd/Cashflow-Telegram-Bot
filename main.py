import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, LEADS_CHANNEL_ID
import start
from database import init_db, migrate_db, sync_with_sheets, db_get_funnel_stats
from scheduler_manager import scheduler 

logging.basicConfig(level=logging.INFO)

# YANGI FUNKSIYA: Har soat yuboriladigan hisobot
async def send_hourly_report(bot: Bot):
    try:
        users = db_get_funnel_stats()
        if not users:
            return
            
        steps_data = {}
        for u_id, uname, step in users:
            current = step if step else "Boshlash (Start)"
            if current not in steps_data:
                steps_data[current] = []
            steps_data[current].append((u_id, uname))

        total = len(users)
        msg = f"📊 <b>Soatlik Voronka Hisoboti</b>\n\n👥 Umumiy mijozlar (Leadlar): <b>{total}</b> ta\n\n"

        for step_name, u_list in sorted(steps_data.items()):
            msg += f"📍 <b>{step_name}</b> ({len(u_list)} ta):\n"
            
            links = []
            for u_id, uname in u_list:
                name_clean = uname.replace('<', '').replace('>', '') if uname else f"ID:{u_id}"
                if name_clean == "Noma'lum" or not name_clean.strip():
                    name_clean = f"Mijoz {u_id}"
                
                # tg://user?id= orqali username bo'lmasa ham to'g'ridan to'g'ri profilga o'tish mumkin
                links.append(f'<a href="tg://user?id={u_id}">{name_clean}</a>')
            
            # Agar list uzun bo'lib ketsa, ekranni egallamaslik uchun qisqartiramiz
            if len(links) > 70:
                msg += ", ".join(links[:70]) + f" ... va yana {len(links)-70} ta.\n\n"
            else:
                msg += ", ".join(links) + "\n\n"
        
        # Telegram xabar chegarasi (4096 belgi) dan oshsa bo'lib jo'natish
        if len(msg) > 4000:
            parts = [msg[i:i+4000] for i in range(0, len(msg), 4000)]
            for part in parts:
                await bot.send_message(LEADS_CHANNEL_ID, part, parse_mode="HTML")
        else:
            await bot.send_message(LEADS_CHANNEL_ID, msg, parse_mode="HTML")
            
    except Exception as e:
        print(f"Hisobot yuborishda xatolik: {e}")

async def main():
    init_db()
    migrate_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start.router)

    scheduler.start()

    scheduler.add_job(
        sync_with_sheets, 
        'interval', 
        minutes=10, 
        id='sync_job', 
        replace_existing=True
    )
    
    # YANGILANISH: Hisobot schedulerni ulash
    scheduler.add_job(
        send_hourly_report,
        'interval',
        hours=1,  # Har 1 soatda
        args=[bot],
        id='hourly_report_job',
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