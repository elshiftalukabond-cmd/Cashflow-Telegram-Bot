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
    credentials = Credentials.from_service_account_file("excel-maktabi-cashflow-bot.json", scopes=scopes)
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

def update_user_form(user_id, username, niche, revenue, accounting, phone):
    try:
        sheet = get_sheet()
        if not sheet: return
        
        cell = sheet.find(str(user_id), in_column=1)
        if cell:
            row = cell.row
            sheet.update(range_name=f"B{row}:F{row}", values=[[username, niche, revenue, accounting, phone]])
        else:
            sheet.append_row([str(user_id), username, niche, revenue, accounting, phone])
    except Exception as e:
        print(f"Anketa yangilashda xatolik: {e}")