from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from texts import TEXTS

def get_step1_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS['btn_step_1'], callback_data="step_2")]])

def get_step2_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS['btn_step_2'], callback_data="case_1")]])

def get_case1_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS['btn_case_1'], callback_data="case_2")]])

def get_case2_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS['btn_case_2'], callback_data="case_3")]])

def get_case3_kb():
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=TEXTS['btn_case_3'], callback_data="step_6")]])

def get_main_actions_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS['btn_buy'], callback_data="buy_main")],
        [InlineKeyboardButton(text=TEXTS['btn_form'], callback_data="fill_form")],
        [InlineKeyboardButton(text=TEXTS['btn_contact'], callback_data="contact_admin")]
    ])

def get_revenue_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS['rev_1'], callback_data="rev_1")],
        [InlineKeyboardButton(text=TEXTS['rev_2'], callback_data="rev_2")],
        [InlineKeyboardButton(text=TEXTS['rev_3'], callback_data="rev_3")],
        [InlineKeyboardButton(text=TEXTS['rev_4'], callback_data="rev_4")]
    ])

def get_accounting_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS['acc_1'], callback_data="acc_1")],
        [InlineKeyboardButton(text=TEXTS['acc_2'], callback_data="acc_2")],
        [InlineKeyboardButton(text=TEXTS['acc_3'], callback_data="acc_3")]
    ])

def get_contact_only_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS['btn_contact'], callback_data="contact_admin")]
    ])

def get_buy_form_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS['btn_buy'], callback_data="buy_main")],
        [InlineKeyboardButton(text=TEXTS['btn_form'], callback_data="fill_form")]
    ])

def get_after_buy_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS['btn_form'], callback_data="fill_form")],
        [InlineKeyboardButton(text=TEXTS['btn_contact'], callback_data="contact_admin")]
    ])

def get_nurture_1_kb():
    return get_buy_form_kb()

def get_nurture_2_kb():
    return get_buy_form_kb()

def get_nurture_3_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=TEXTS['btn_buy_act'], callback_data="buy_main")],
        [InlineKeyboardButton(text=TEXTS['btn_form'], callback_data="fill_form")],
        [InlineKeyboardButton(text=TEXTS['btn_not_now'], callback_data="not_now")]
    ])