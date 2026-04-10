import asyncio
import datetime
import pytz
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.filters import Command
import ast
import config
import inline
from texts import TEXTS
from states import RegState
from database import db_save_start, db_update_form, db_update_step, get_all_users 
from scheduler_manager import scheduler

router = Router()
user_forms_cache = {}

# ================= YORDAMCHI FUNKSIYALAR =================
def cancel_funnel(user_id: int):
    job_id = f"funnel_{user_id}"
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)

async def safe_send_message(bot: Bot, chat_id: int, *args, **kwargs):
    try:
        return await bot.send_message(chat_id, *args, **kwargs)
    except TelegramForbiddenError:
        pass
    except Exception as e:
        print(f"Xabar yuborishda xatolik {chat_id}: {e}")
    return None

async def clear_markup(bot: Bot, chat_id: int, message_id: int):
    if message_id:
        try:
            await bot.edit_message_reply_markup(chat_id=chat_id, message_id=message_id, reply_markup=None)
        except: pass

async def send_video_block(bot: Bot, chat_id: int, intro_text: str, video_data, footer_text: str, markup=None):
    if intro_text:
        await safe_send_message(bot, chat_id, text=intro_text, parse_mode="HTML")
    
    if isinstance(video_data, str):
        try:
            video_data = ast.literal_eval(video_data)
        except (ValueError, SyntaxError):
            pass 

    if isinstance(video_data, int) or (isinstance(video_data, str) and video_data.isdigit()):
        video_ids = [int(video_data)]
    elif isinstance(video_data, list) or isinstance(video_data, tuple):
        video_ids = video_data
    else:
        video_ids = []

    for vid in video_ids:
        if vid:
            try:
                await bot.copy_message(chat_id, config.CHANNEL_ID, int(vid))
                await asyncio.sleep(0.5) 
            except Exception as e:
                print(f"Video xato (ID: {vid}): {e}")
            
    if footer_text:
        msg = await safe_send_message(bot, chat_id, text=footer_text, reply_markup=markup, parse_mode="HTML")
        return msg.message_id if msg else None
        
    return None

async def send_nurture_msg(chat_id: int, day_num: int):
    bot = Bot(token=config.BOT_TOKEN)
    try:
        if day_num == 1:
            await safe_send_message(bot, chat_id, text=TEXTS['nurture_1'], reply_markup=inline.get_nurture_1_kb(), parse_mode="HTML")
        elif day_num == 2:
            try: 
                if config.NURTURE_VIDEO_2:
                    await bot.copy_message(chat_id, config.CHANNEL_ID, config.NURTURE_VIDEO_2)
            except: pass
            await safe_send_message(bot, chat_id, text=TEXTS['nurture_2'], reply_markup=inline.get_nurture_2_kb(), parse_mode="HTML")
        elif day_num == 3:
            await safe_send_message(bot, chat_id, text=TEXTS['nurture_3'], reply_markup=inline.get_nurture_3_kb(), parse_mode="HTML")
    except Exception as e:
        print(f"Nurture xatosi: {e}")
    finally:
        await bot.session.close()

# ================= KAFOLATLANGAN AVTOVORONKA FUNKSIYALARI (YANGILANDI) =================

async def run_auto_step_2(chat_id: int, prev_msg_id: int):
    bot = Bot(token=config.BOT_TOKEN)
    try:
        db_update_step(chat_id, "1. 1-qadam (Video)") # <--- Qadam yangilandi
        await clear_markup(bot, chat_id, prev_msg_id)
        msg_id = await send_video_block(bot, chat_id, None, config.STEP2_VIDEO_ID, TEXTS['step_2'], inline.get_step2_kb())
        if msg_id: schedule_funnel_job(chat_id, 'case_1', 1200, msg_id)
    finally:
        await bot.session.close()

async def run_auto_case_1(chat_id: int, prev_msg_id: int):
    bot = Bot(token=config.BOT_TOKEN)
    try:
        db_update_step(chat_id, "2. Case 1 bosqichi") # <--- Qadam yangilandi
        await clear_markup(bot, chat_id, prev_msg_id)
        msg_id = await send_video_block(bot, chat_id, TEXTS['case_1_intro'], config.CASE1_VIDEO_ID, TEXTS['case_1_footer'], inline.get_case1_kb())
        if msg_id: schedule_funnel_job(chat_id, 'case_2', 1200, msg_id)
    finally:
        await bot.session.close()

async def run_auto_case_2(chat_id: int, prev_msg_id: int):
    bot = Bot(token=config.BOT_TOKEN)
    try:
        db_update_step(chat_id, "3. Case 2 bosqichi") # <--- Qadam yangilandi
        await clear_markup(bot, chat_id, prev_msg_id)
        msg_id = await send_video_block(bot, chat_id, TEXTS['case_2_intro'], config.CASE2_VIDEO_ID, TEXTS['case_2_footer'], inline.get_case2_kb())
        if msg_id: schedule_funnel_job(chat_id, 'case_3', 1200, msg_id)
    finally:
        await bot.session.close()

async def run_auto_case_3(chat_id: int, prev_msg_id: int):
    bot = Bot(token=config.BOT_TOKEN)
    try:
        db_update_step(chat_id, "4. Case 3 bosqichi") # <--- Qadam yangilandi
        await clear_markup(bot, chat_id, prev_msg_id)
        msg_id = await send_video_block(bot, chat_id, TEXTS['case_3_intro'], config.CASE3_VIDEO_ID, TEXTS['case_3_footer'], inline.get_case3_kb())
        if msg_id: schedule_funnel_job(chat_id, 'step_6', 1200, msg_id)
    finally:
        await bot.session.close()

async def run_auto_step_6(chat_id: int, prev_msg_id: int):
    bot = Bot(token=config.BOT_TOKEN)
    try:
        db_update_step(chat_id, "5. Demo video bosqichi") # <--- Qadam yangilandi
        await clear_markup(bot, chat_id, prev_msg_id)
        msg_id = await send_video_block(bot, chat_id, None, config.DEMO_VIDEO_ID, TEXTS['step_6'], inline.get_step6_kb())
        if msg_id: schedule_funnel_job(chat_id, 'step_7', 180, msg_id)
    finally:
        await bot.session.close()

async def run_auto_step_7(chat_id: int, prev_msg_id: int):
    bot = Bot(token=config.BOT_TOKEN)
    try:
        db_update_step(chat_id, "6. Sotuv taklifini ko'rdi") # <--- QADAM YANGILANDI (Endi bu bosqichda hisobot o'zgaradi)
        await clear_markup(bot, chat_id, prev_msg_id)
        await safe_send_message(bot, chat_id, text=TEXTS['step_7'], reply_markup=inline.get_main_actions_kb(), parse_mode="HTML")
    finally:
        await bot.session.close()

def schedule_funnel_job(chat_id: int, step_name: str, delay_seconds: int, prev_msg_id: int):
    run_date = datetime.datetime.now(pytz.timezone('Asia/Tashkent')) + datetime.timedelta(seconds=delay_seconds)
    job_id = f"funnel_{chat_id}"
    
    cancel_funnel(chat_id)
        
    func_map = {
        'step_2': run_auto_step_2,
        'case_1': run_auto_case_1,
        'case_2': run_auto_case_2,
        'case_3': run_auto_case_3,
        'step_6': run_auto_step_6,
        'step_7': run_auto_step_7
    }
    
    scheduler.add_job(
        func_map[step_name],
        'date',
        run_date=run_date,
        args=[chat_id, prev_msg_id],
        id=job_id,
        replace_existing=True
    )

# ================= ASOSIY HANDLERLAR =================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else "Noma'lum"
    
    db_save_start(user_id, username)
    db_update_step(user_id, "0. Start bosildi") # <--- O'ZGARISH
    
    for i in [1, 2, 3]:
        job_id = f"nurture_{user_id}_{i}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

    h, m = map(int, config.NURTURE_TIME.split(":"))
    tz = pytz.timezone('Asia/Tashkent')
    
    for i, day_ahead in enumerate([config.NURTURE_DAY_1, config.NURTURE_DAY_2, config.NURTURE_DAY_3], 1):
        run_date = datetime.datetime.now(tz) + datetime.timedelta(days=day_ahead)
        run_date = run_date.replace(hour=h, minute=m, second=0, microsecond=0)
        
        if run_date < datetime.datetime.now(tz):
            run_date += datetime.timedelta(days=1)

        scheduler.add_job(
            send_nurture_msg, 
            'date', 
            run_date=run_date, 
            args=[user_id, i], 
            id=f"nurture_{user_id}_{i}"
        )

    cancel_funnel(user_id) 
    msg = await message.answer(TEXTS['step_1'], reply_markup=inline.get_step1_kb(), parse_mode="HTML")
    schedule_funnel_job(user_id, 'step_2', 1200, msg.message_id)

@router.callback_query(F.data == "step_2")
async def process_step_2(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "1. 1-qadam (Video)") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    msg_id = await send_video_block(callback.bot, user_id, None, config.STEP2_VIDEO_ID, TEXTS['step_2'], inline.get_step2_kb())
    if msg_id: schedule_funnel_job(user_id, 'case_1', 1200, msg_id)
    await callback.answer()

@router.callback_query(F.data == "case_1")
async def process_case_1(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "2. Case 1 bosqichi") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    msg_id = await send_video_block(callback.bot, user_id, TEXTS['case_1_intro'], config.CASE1_VIDEO_ID, TEXTS['case_1_footer'], inline.get_case1_kb())
    if msg_id: schedule_funnel_job(user_id, 'case_2', 1200, msg_id)
    await callback.answer()

@router.callback_query(F.data == "case_2")
async def process_case_2(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "3. Case 2 bosqichi") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    msg_id = await send_video_block(callback.bot, user_id, TEXTS['case_2_intro'], config.CASE2_VIDEO_ID, TEXTS['case_2_footer'], inline.get_case2_kb())
    if msg_id: schedule_funnel_job(user_id, 'case_3', 1200, msg_id)
    await callback.answer()

@router.callback_query(F.data == "case_3")
async def process_case_3(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "4. Case 3 bosqichi") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    msg_id = await send_video_block(callback.bot, user_id, TEXTS['case_3_intro'], config.CASE3_VIDEO_ID, TEXTS['case_3_footer'], inline.get_case3_kb())
    if msg_id: schedule_funnel_job(user_id, 'step_6', 1200, msg_id)
    await callback.answer()

@router.callback_query(F.data == "step_6")
async def process_step_6(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "5. Demo video bosqichi") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    msg_id = await send_video_block(callback.bot, user_id, None, config.DEMO_VIDEO_ID, TEXTS['step_6'], inline.get_step6_kb())
    if msg_id: schedule_funnel_job(user_id, 'step_7', 180, msg_id)
    await callback.answer()

@router.callback_query(F.data == "step_7")
async def process_step_7(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "6. Sotuv taklifini ko'rdi")
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(TEXTS['step_7'], reply_markup=inline.get_main_actions_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "not_now")
async def process_not_now(callback: CallbackQuery):
    user_id = callback.from_user.id
    db_update_step(user_id, "Do'jim: Hozir emas") # <--- O'ZGARISH
    await callback.message.edit_text(TEXTS['ans_not_now'])
    await callback.answer()

@router.callback_query(F.data == "buy_main")
async def process_buy_main(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id) 
    db_update_step(user_id, "Sotib olishni bosdi") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(TEXTS['buy_msg'], reply_markup=inline.get_after_buy_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "fill_form")
async def process_fill_form(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "📝 Anketa boshladi (niche)") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    await state.set_state(RegState.niche)
    await callback.message.answer(TEXTS['form_intro'], parse_mode="HTML")
    await callback.message.answer(TEXTS['form_q1'], parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "contact_admin")
async def process_contact_admin(callback: CallbackQuery):
    user_id = callback.from_user.id
    cancel_funnel(user_id)
    db_update_step(user_id, "Admin bilan bog'lanish") # <--- O'ZGARISH
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(TEXTS['contact_msg'], reply_markup=inline.get_buy_form_kb(), parse_mode="HTML")
    await callback.answer()

@router.message(RegState.niche)
async def form_niche(message: Message, state: FSMContext):
    user_id = message.from_user.id
    db_update_step(user_id, "📝 Anketa (Aylanma so'ralyapti)") # <--- O'ZGARISH
    await state.update_data(niche=message.text)
    await state.set_state(RegState.revenue)
    await message.answer(TEXTS['form_q2'], reply_markup=inline.get_revenue_kb(), parse_mode="HTML")

@router.callback_query(RegState.revenue)
async def form_revenue(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    db_update_step(user_id, "📝 Anketa (Uchyot so'ralyapti)") # <--- O'ZGARISH
    rev_map = {"rev_1": TEXTS['rev_1'], "rev_2": TEXTS['rev_2'], "rev_3": TEXTS['rev_3'], "rev_4": TEXTS['rev_4']}
    val = rev_map.get(callback.data, "Noma'lum")
    await state.update_data(revenue=val)
    await callback.message.edit_text(f"{TEXTS['form_q2']}\n\n✅ <i>{val}</i>", parse_mode="HTML")
    await state.set_state(RegState.accounting)
    await callback.message.answer(TEXTS['form_q3'], reply_markup=inline.get_accounting_kb(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(RegState.accounting)
async def form_accounting(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    db_update_step(user_id, "📝 Anketa (Telefon so'ralyapti)") # <--- O'ZGARISH
    acc_map = {"acc_1": TEXTS['acc_1'], "acc_2": TEXTS['acc_2'], "acc_3": TEXTS['acc_3']}
    val = acc_map.get(callback.data, "Noma'lum")
    await state.update_data(accounting=val)
    await callback.message.edit_text(f"{TEXTS['form_q3']}\n\n✅ <i>{val}</i>", parse_mode="HTML")
    await state.set_state(RegState.phone)
    await callback.message.answer(TEXTS['form_q4'], parse_mode="HTML")
    await callback.answer()

@router.message(RegState.phone)
async def form_phone(message: Message, state: FSMContext):
    if not message.text: return await message.answer(TEXTS['err_phone'])
    phone = message.text.strip()
    check_phone = phone.replace("+", "").replace(" ", "")
    if not check_phone.isdigit() or len(check_phone) < 7:
        return await message.answer(TEXTS['err_phone'])

    await state.update_data(phone=phone)
    data = await state.get_data()
    niche, revenue, accounting = data.get('niche', ""), data.get('revenue', ""), data.get('accounting', "")
    username = f"@{message.from_user.username}" if message.from_user.username else "Noma'lum"
    user_id = message.from_user.id
    
    # db_update_form chaqirilganda 'current_step' ni '✅ Anketa toliq tugatildi' qilib o'zgartiradi
    db_update_form(user_id, username, niche, revenue, accounting, phone) 
    
    tz = pytz.timezone("Asia/Tashkent")
    hozirgi_vaqt = datetime.datetime.now(tz).strftime("%Y-%m-%d %H:%M")

    admin_text = (
        f"🔥 <b>YANGI ZAYAVKA!</b>\n\n"
        f"📅 <b>Vaqt:</b> {hozirgi_vaqt}\n"
        f"🏢 <b>Biznes:</b> {niche}\n"
        f"💰 <b>Aylanma:</b> {revenue}\n"
        f"📊 <b>Hisob:</b> {accounting}\n"
        f"📞 <b>Telefon:</b> {phone}\n"
        f"🔗 <b>Username:</b> {username}\n"
        f"🆔 <b>TG ID:</b> <code>{user_id}</code>"
    )
    
    try:
        if config.LEADS_CHANNEL_ID:
            await message.bot.send_message(chat_id=config.LEADS_CHANNEL_ID, text=admin_text, parse_mode="HTML")
    except Exception as e:
        print(f"Zayavkani kanalga yuborishda xato: {e}")

    await state.clear()
    await message.answer(TEXTS['form_finish'], reply_markup=inline.get_contact_only_kb(), parse_mode="HTML")

@router.message(Command("test_nurture"))
async def test_nurture_msgs(message: Message):
    user_id = message.from_user.id
    await message.answer("🛠 <b>Test boshlandi:</b> Kunlik xabarlar ketma-ket yuborilmoqda...", parse_mode="HTML")
    await send_nurture_msg(user_id, 1)
    await asyncio.sleep(3) 
    await send_nurture_msg(user_id, 2)
    await asyncio.sleep(3)
    await send_nurture_msg(user_id, 3)
    await message.answer("✅ <b>Test yakunlandi!</b>", parse_mode="HTML")

@router.message(Command("xatoni_tuzatish"))
async def xatoni_tuzatish_cmd(message: Message):
    users = get_all_users()
    await message.answer(f"🚀 Barcha {len(users)} ta foydalanuvchini tutib olish boshlandi...")
    
    # Eslatma: O'zingiz yoqtirgan stiker ID sini qo'yishingiz mumkin. Hozircha bo'sh qoldirsangiz faqat text boradi.
    sticker_id = "CAACAgIAAxkBAAE..." 
    
    text = (
        "<b>Nimadir xato ketdimi? 🤔</b>\n\n"
        "Biroz muddat avval texnik qiyinchiliklar tufayli avtovoronkamizdagi "
        "ayrim xabarlar sizga kelmay qolgan bo'lishi mumkin.\n\n"
        "Shu kabi xatolik sizning biznesingizda qolib ketmasligi amaliy ishlar sizni kutib turibdi!\n"
        "Agar oldingi bosqichlarda qolib ketgan bo'lsangiz, davom etish turini o'zingiz tanlang 👇"
    )
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Boshidan boshlash 🔄", callback_data="restart_funnel")],
        [InlineKeyboardButton(text="Sotuv taklifini ko'rish ➡️", callback_data="step_7")]
    ])
    
    count = 0
    for u_id in users:
        try:
            # Agar sticker ishlamasa, u tashlab o'tiladi
            try:
                if sticker_id.startswith("CAACA"):
                    await message.bot.send_sticker(u_id, sticker=sticker_id)
            except:
                pass
                
            await message.bot.send_message(u_id, text=text, reply_markup=kb, parse_mode="HTML")
            count += 1
            await asyncio.sleep(0.1) # limitga tushmaslik uchun
        except Exception as e:
            print(f"Xato (ID: {u_id}): {e}")
            
    await message.answer(f"✅ Qayta tutib olish yakunlandi! {count} kishiga yuborildi.")

@router.callback_query(F.data == "restart_funnel")
async def process_restart_funnel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = callback.from_user.id
    username = f"@{callback.from_user.username}" if callback.from_user.username else "Noma'lum"
    
    db_save_start(user_id, username)
    db_update_step(user_id, "0. Start bosildi")
    
    for i in [1, 2, 3]:
        job_id = f"nurture_{user_id}_{i}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

    h, m = map(int, config.NURTURE_TIME.split(":"))
    tz = pytz.timezone('Asia/Tashkent')
    
    for i, day_ahead in enumerate([config.NURTURE_DAY_1, config.NURTURE_DAY_2, config.NURTURE_DAY_3], 1):
        run_date = datetime.datetime.now(tz) + datetime.timedelta(days=day_ahead)
        run_date = run_date.replace(hour=h, minute=m, second=0, microsecond=0)
        
        if run_date < datetime.datetime.now(tz):
            run_date += datetime.timedelta(days=1)

        scheduler.add_job(
            send_nurture_msg, 
            'date', 
            run_date=run_date, 
            args=[user_id, i], 
            id=f"nurture_{user_id}_{i}"
        )

    cancel_funnel(user_id) 
    await callback.message.delete()
    msg = await callback.message.answer(TEXTS['step_1'], reply_markup=inline.get_step1_kb(), parse_mode="HTML")
    schedule_funnel_job(user_id, 'step_2', 1200, msg.message_id)
    await callback.answer("Boshidan boshlandi!")