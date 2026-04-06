import sqlite3
import os
import asyncio
from sheets import update_user_form, save_user_start

os.makedirs("data", exist_ok=True)
DB_NAME = "data/bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            username TEXT,
            niche TEXT,
            revenue TEXT,
            accounting TEXT,
            phone TEXT,
            is_synced INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def db_save_start(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)', (str(user_id), username))
    cursor.execute('UPDATE users SET username=? WHERE user_id=?', (username, str(user_id)))
    conn.commit()
    conn.close()

def db_update_form(user_id, username, niche, revenue, accounting, phone):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET username=?, niche=?, revenue=?, accounting=?, phone=?, is_synced=0 
        WHERE user_id=?
    ''', (username, niche, revenue, accounting, phone, str(user_id)))
    conn.commit()
    conn.close()

async def sync_with_sheets():
    """Google Sheets ga jo'natish (botni qotirib qo'ymaslik uchun to_thread ishlatiladi)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Eskidan saqlanib qolgan bazada qoshimcha ustunlar bo'lsa ham xato bermasligi uchun 
    # faqat kerakli ustunlarni aniq Select qilamiz
    try:
        cursor.execute('SELECT user_id, username, niche, revenue, accounting, phone FROM users WHERE is_synced=0')
        unsynced = cursor.fetchall()
        
        for row in unsynced:
            u_id, u_name, niche, rev, acc, phone = row
            try:
                await asyncio.to_thread(save_user_start, u_id, u_name)
                if niche:
                    await asyncio.to_thread(update_user_form, u_id, u_name, niche, rev, acc, phone)
                
                cursor.execute('UPDATE users SET is_synced=1 WHERE user_id=?', (u_id,))
                conn.commit()
            except Exception as e:
                print(f"Sheets Sinxronizatsiya xatosi {u_id}: {e}")
    except Exception as e:
        print(f"DB bilan ishlashda xatolik: {e}")
    finally:
        conn.close()