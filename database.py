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

    # O'ZGARISH: current_step ustuni qo'shildi
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
            current_step TEXT DEFAULT 'Start'
        )
    ''')

    conn.commit()
    conn.close()


# 🚀 START bosilganda
def db_save_start(user_id, username):
    date_str, time_str = get_current_datetime()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # O'ZGARISH: 'current_step' qo'shildi va parametrlar to'g'ri uzatildi
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, created_date, created_time, current_step)
        VALUES (?, ?, ?, ?, '0. Start bosildi')
    ''', (str(user_id), username, date_str, time_str))

    # O'ZGARISH: Username bilan birga qadam ham yangilanadi
    cursor.execute('''
        UPDATE users 
        SET username=?, current_step='0. Start bosildi' 
        WHERE user_id=?
    ''', (username, str(user_id)))

    conn.commit()
    conn.close()


# ================= YANGI FUNKSIYALAR =================

# 📍 Qadamni yangilab borish uchun
def db_update_step(user_id, step_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET current_step=? WHERE user_id=?', (step_name, str(user_id)))
    conn.commit()
    conn.close()

# 📊 Kanalga hisobot yuborish uchun barcha leadlarni olish
def get_leads_status():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, username, current_step FROM users')
    rows = cursor.fetchall()
    conn.close()
    return rows

# 📥 Barcha userlarni olish (Broadcast uchun)
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    rows = [row[0] for row in cursor.fetchall()]
    conn.close()
    return rows

# =====================================================


# 📝 Forma to‘ldirilganda
def db_update_form(user_id, username, niche, revenue, accounting, phone):
    # Toshkent vaqtini aniqlash:
    date_str, time_str = get_current_datetime()
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # O'ZGARISH: Anketa tugatilganda 'current_step' ham yangilanadi
    cursor.execute('''
        UPDATE users 
        SET username=?, niche=?, revenue=?, accounting=?, phone=?, 
            created_date=?, created_time=?, is_synced=0, current_step='✅ Anketa toliq tugatildi'
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
                success = await asyncio.to_thread(
                    update_user_form,
                    u_id, u_name, niche, rev, acc, phone, c_date, c_time
                )

                if success:
                    # Sync bo‘ldi deb belgilash
                    cursor.execute(
                        'UPDATE users SET is_synced=1 WHERE user_id=?',
                        (u_id,)
                    )
                    conn.commit()
                else:
                    print(f"[SYNC FAILED]: Google Sheets qaytarildi: False. User ID: {u_id}")

                # Rate limitdan saqlanish
                await asyncio.sleep(0.5)

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

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN current_step TEXT DEFAULT 'Start'")
    except:
        pass

    conn.commit()
    conn.close()

async def recover_unsynced_users_from_sheet():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        # Barcha forma to'ldirganlarni olamiz
        cursor.execute('''
            SELECT user_id, username, niche, revenue, accounting, phone, created_date, created_time 
            FROM users 
            WHERE current_step='✅ Anketa toliq tugatildi'
        ''')
        finished_users = cursor.fetchall()
        
        from sheets import get_sheet
        
        # Async emasligi sabab blocklanmasligi uchun to_thread ham ishlatish mumkin 
        # ammo startupda ekanligi uchun to'g'ridan to'g'ri ishlataveramiz.
        def fetch_sheet_ids():
            sheet = get_sheet()
            if not sheet: return None
            # update_user_form orqali tushganlar C (3-chi) ustunda 
            return sheet.col_values(3)

        col_c_values = await asyncio.to_thread(fetch_sheet_ids)

        if col_c_values is None:
            print("Google Sheet topilmadi, tiklash bekor qilindi.")
            return

        sheet_form_ids = set([str(val).strip() for val in col_c_values])

        recovered_count = 0
        for row in finished_users:
            u_id, u_name, niche, rev, acc, phone, c_date, c_time = row
            u_id_str = str(u_id).strip()
            
            # Agar sheetdagi 3-ustunda bu user_id bo'lmasa, demak formasi yuklanmagan
            if u_id_str not in sheet_form_ids:
                print(f"[RECOVERY] {u_name} (ID: {u_id}) jadvalda yo'q, qayta yuklanmoqda...")
                success = await asyncio.to_thread(
                    update_user_form,
                    u_id, u_name, niche, rev, acc, phone, c_date, c_time
                )
                if success:
                    recovered_count += 1
                    # uning is_synced flagini ham 1 ga majburan to'g'irlab qo'yamiz
                    cursor.execute('UPDATE users SET is_synced=1 WHERE user_id=?', (u_id,))
                    conn.commit()
                await asyncio.sleep(0.5)

        print(f"[RECOVERY] Majburiy tekshiruv va tiklash tugatildi! {recovered_count} ta qolib ketgan profil yuklandi.")

    except Exception as e:
        print(f"[RECOVERY ERROR]: {e}")
    finally:
        conn.close()