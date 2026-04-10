import sqlite3
import datetime
import pytz
import os
import asyncio
from sheets import update_user_form

os.makedirs("data", exist_ok=True)
DB_NAME = "data/bot_data.db"

def get_current_datetime():
    tz = pytz.timezone("Asia/Tashkent")
    now = datetime.datetime.now(tz)
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

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
            created_date TEXT,
            created_time TEXT,
            is_synced INTEGER DEFAULT 0,
            current_step TEXT DEFAULT 'Boshlash (Start)'
        )
    ''')
    conn.commit()
    conn.close()

def db_save_start(user_id, username):
    date_str, time_str = get_current_datetime()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, created_date, created_time, current_step)
        VALUES (?, ?, ?, ?, '0. Start bosildi')
    ''', (str(user_id), username, date_str, time_str))
    
    cursor.execute('''
        UPDATE users SET username=? WHERE user_id=?
    ''', (username, str(user_id)))
    conn.commit()
    conn.close()

def db_update_form(user_id, username, niche, revenue, accounting, phone):
    date_str, time_str = get_current_datetime()
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users 
        SET username=?, niche=?, revenue=?, accounting=?, phone=?, 
            created_date=?, created_time=?, is_synced=0 
        WHERE user_id=?
    ''', (username, niche, revenue, accounting, phone, date_str, time_str, str(user_id)))
    conn.commit()
    conn.close()

# YANGI FUNKSIYA: Foydalanuvchi qadamini yangilash
def db_update_step(user_id, step_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE users SET current_step=? WHERE user_id=?
    ''', (step_name, str(user_id)))
    conn.commit()
    conn.close()

# YANGI FUNKSIYA: Hisobot uchun barcha leadlarni olish
def db_get_funnel_stats():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Faqat bot bloklamaganlarni bilish imkonsiz, shuning hammasini olamiz
    cursor.execute('SELECT user_id, username, current_step FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

async def sync_with_sheets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT user_id, username, niche, revenue, accounting, phone, created_date, created_time 
            FROM users WHERE is_synced=0
        ''')
        unsynced = cursor.fetchall()
        for row in unsynced:
            u_id, u_name, niche, rev, acc, phone, c_date, c_time = row
            try:
                await asyncio.to_thread(update_user_form, u_id, u_name, niche, rev, acc, phone, c_date, c_time)
                cursor.execute('UPDATE users SET is_synced=1 WHERE user_id=?', (u_id,))
                conn.commit()
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"[SYNC ERROR] user {u_id}: {e}")
    except Exception as e:
        print(f"[DB ERROR]: {e}")
    finally:
        conn.close()

def migrate_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try: cursor.execute("ALTER TABLE users ADD COLUMN created_date TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE users ADD COLUMN created_time TEXT")
    except: pass
    try: cursor.execute("ALTER TABLE users ADD COLUMN is_synced INTEGER DEFAULT 0")
    except: pass
    # YANGILANISH: Xavfsiz tarzda yangi ustun qo'shish
    try: cursor.execute("ALTER TABLE users ADD COLUMN current_step TEXT DEFAULT 'Boshlash (Start)'")
    except: pass
    conn.commit()
    conn.close()