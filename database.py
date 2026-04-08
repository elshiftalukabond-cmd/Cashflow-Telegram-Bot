import sqlite3
import datetime
import pytz
import os
import asyncio
from sheets import update_user_form

# Papka yaratish
os.makedirs("data", exist_ok=True)

DB_NAME = "data/bot_data.db"


# 📅 Vaqt olish
def get_current_datetime():
    tz = pytz.timezone("Asia/Tashkent")
    now = datetime.datetime.now(tz)
    return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")


# 🧱 DB init
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
            is_synced INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()


# 🚀 START bosilganda
def db_save_start(user_id, username):
    date_str, time_str = get_current_datetime()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Agar user yo'q bo‘lsa qo‘shadi
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, created_date, created_time)
        VALUES (?, ?, ?, ?)
    ''', (str(user_id), username, date_str, time_str))

    # Username yangilanadi
    cursor.execute('''
        UPDATE users 
        SET username=? 
        WHERE user_id=?
    ''', (username, str(user_id)))

    conn.commit()
    conn.close()


# 📝 Forma to‘ldirilganda
def db_update_form(user_id, username, niche, revenue, accounting, phone):
    # Toshkent vaqtini aniqlash:
    date_str, time_str = get_current_datetime()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # created_date va created_time ni ham YANGILAYMIZ
    cursor.execute('''
        UPDATE users 
        SET username=?, niche=?, revenue=?, accounting=?, phone=?, 
            created_date=?, created_time=?, is_synced=0 
        WHERE user_id=?
    ''', (username, niche, revenue, accounting, phone, date_str, time_str, str(user_id)))

    conn.commit()
    conn.close()


# 🔄 Google Sheets sync
async def sync_with_sheets():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT user_id, username, niche, revenue, accounting, phone, created_date, created_time 
            FROM users 
            WHERE is_synced=0
        ''')

        unsynced = cursor.fetchall()

        for row in unsynced:
            u_id, u_name, niche, rev, acc, phone, c_date, c_time = row

            try:
                # Sheetsga async yuborish
                await asyncio.to_thread(
                    update_user_form,
                    u_id, u_name, niche, rev, acc, phone, c_date, c_time
                )

                # Sync bo‘ldi deb belgilash
                cursor.execute(
                    'UPDATE users SET is_synced=1 WHERE user_id=?',
                    (u_id,)
                )
                conn.commit()

                # Rate limitdan saqlanish
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

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_date TEXT")
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN created_time TEXT")
    except:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN is_synced INTEGER DEFAULT 0")
    except:
        pass

    conn.commit()
    conn.close()