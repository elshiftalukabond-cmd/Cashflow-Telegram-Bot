import gspread
import os
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

load_dotenv()
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

scopes = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_sheet():
    if not SPREADSHEET_ID: return None
    credentials = Credentials.from_service_account_file("GOOGLE_CREDENTIALS", scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_key(SPREADSHEET_ID).sheet1

def save_user_start(user_id, username):
    try:
        sheet = get_sheet()
        if not sheet: return
        
        cell = sheet.find(str(user_id), in_column=1)
        
        if cell:
            sheet.update_cell(cell.row, 2, username)
        else:
            # UMUMAN YANGI USER bo'lsa, start bosilishi bilan ID saqlanadi
            sheet.append_row([str(user_id), username, "", "", "", ""])
    except Exception as e:
        print(f"Start saqlashda xatolik: {e}")

def update_user_form(user_id, username, niche, revenue, accounting, phone, created_date, created_time):
    try:
        sheet = get_sheet()
        if not sheet:
            return

        sheet.append_row([
            created_date,   # A
            created_time,   # B
            str(user_id),   # C
            username,       # D
            niche,          # E
            revenue,        # F
            accounting,     # G
            phone           # H
        ])

    except Exception as e:
        print(f"Sheets yozishda xatolik: {e}")