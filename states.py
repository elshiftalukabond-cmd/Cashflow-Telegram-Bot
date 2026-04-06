from aiogram.fsm.state import State, StatesGroup

class RegState(StatesGroup):
    niche = State()       # Biznes sohasi
    revenue = State()     # Oylik aylanma
    accounting = State()  # Uchyot
    phone = State()       # Telefon