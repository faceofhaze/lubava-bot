# handlers.py
import asyncio
import logging
import random
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import FSInputFile, LabeledPrice, PreCheckoutQuery, BufferedInputFile

from config import PRICES, PRIVATE_BONUSES, DONATION_ALERT_URL, MONOBANK_CARD, MONOBANK_URL
from database import Database
from ai_service import AIService
from utils import (
    get_level_info, detect_user_type, get_main_menu, 
    has_video_files, send_random_video, send_kiss_video,
    get_ai_response, get_discounted_price
)

logger = logging.getLogger(__name__)

def register_handlers(dp: Dispatcher, bot: Bot, db: Database, ai_service: AIService):
    
    # ========== КОМАНДИ ==========
    @dp.message(Command("start"))
    async def cmd_start(m: types.Message):
        u_id = str(m.from_user.id)
        user = await db.get_user(u_id)
        
        if not user:
            await db.create_user(u_id)
            await send_random_video(m, "videos", "Привiт! Я Любава\nРозкажи про себе!")
            await m.answer("Тобi нараховано 100 зiрок!")
        else:
            await m.answer(f"З поверненням! Баланс: {user.get('stars', 0)} зiрок")
        
        await m.answer("Меню:", reply_markup=get_main_menu())

    @dp.message(Command("menu"))
    async def cmd_menu(m: types.Message):
        await m.answer("Меню:", reply_markup=get_main_menu())

    # ========== КНОПКИ ==========
    @dp.callback_query(F.data == "status")
    async def show_status(call: types.CallbackQuery):
        u_id = str(call.from_user.id)
        user = await db.get_user(u_id)
        stars = user.get('stars', 0)
        is_private = user.get('private_until', 0) > time.time()
        voices_left = user.get('voice_limit', 0)
        
        text = f"Баланс: {stars} зiрок\nПриват: {'Так' if is_private else 'Нi'}\nГолосових: {voices_left}"
        await call.message.edit_text(text)
        await call.answer()

    @dp.callback_query(F.data == "about_me")
    async def about_me(call: types.CallbackQuery):
        u_id = str(call.from_user.id)
        user = await db.get_user(u_id)
        name = user.get('name', 'невiдомо')
        age = user.get('age', 0)
        gender = user.get('gender', 'невiдомо')
        
        text = f"Ім'я: {name}\nВiк: {age if age > 0 else 'невiдомо'}\nСтать: {gender}"
        await call.message.edit_text(text)
        await call.answer()

    @dp.callback_query(F.data == "clear_history")
    async def clear_history(call: types.CallbackQuery):
        u_id = str(call.from_user.id)
        await db.update_user(u_id, history=[])
        await call.message.edit_text("Iсторiю очищено!")
        await call.answer()

    @dp.callback_query(F.data == "buy_private_30")
    async def buy_private_30(call: types.CallbackQuery):
        u_id = str(call.from_user.id)
        user = await db.get_user(u_id)
        stars = user.get('stars', 0)
        price = 30

        if stars >= price:
            new_stars = stars - price
            new_private = int(time.time() + 30 * 60)
            new_voice = user.get('voice_limit', 0) + 15
            
            await db.update_user(u_id, stars=new_stars, private_until=new_private, voice_limit=new_voice)
            await call.message.edit_text("Приват активовано на 30 хв! +15 голосових")
        else:
            await call.message.edit_text(f"Не вистачає {price - stars} зiрок")
        await call.answer()

    @dp.callback_query(F.data == "buy_private_60")
    async def buy_private_60(call: types.CallbackQuery):
        u_id = str(call.from_user.id)
        user = await db.get_user(u_id)
        stars = user.get('stars', 0)
        price = 50

        if stars >= price:
            new_stars = stars - price
            new_private = int(time.time() + 60 * 60)
            new_voice = user.get('voice_limit', 0) + 30
            
            await db.update_user(u_id, stars=new_stars, private_until=new_private, voice_limit=new_voice)
            await call.message.edit_text("Приват активовано на 60 хв! +30 голосових")
        else:
            await call.message.edit_text(f"Не вистачає {price - stars} зiрок")
        await call.answer()

    @dp.callback_query(F.data == "donate_kiss")
    async def donate_kiss(call: types.CallbackQuery):
        u_id = str(call.from_user.id)
        user = await db.get_user(u_id)
        stars = user.get('stars', 0)

        if stars >= 50:
            new_stars = stars - 50
            await db.update_user(u_id, stars=new_stars)
            
            if has_video_files("video_notes"):
                await send_kiss_video(call.message)
                await call.message.edit_text("Дякую! Отримай вiдео-поцiлунок 💋")
            else:
                await call.message.edit_text("Дякую за пiдтримку!")
        else:
            await call.message.edit_text(f"Не вистачає {50 - stars} зiрок")
        await call.answer()

    @dp.callback_query(F.data == "donation_menu")
    async def donation_menu(call: types.CallbackQuery):
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Купити 100 (Telegram Stars)", callback_data="top_up_stars"))
        
        if DONATION_ALERT_URL:
            builder.row(types.InlineKeyboardButton(text="DonationAlerts", url=DONATION_ALERT_URL))
        if MONOBANK_URL:
            builder.row(types.InlineKeyboardButton(text="Monobank (онлайн)", url=MONOBANK_URL))
        if MONOBANK_CARD:
            builder.row(types.InlineKeyboardButton(text="Monobank (картка)", callback_data="show_monobank_card"))
        
        builder.row(types.InlineKeyboardButton(text="Назад", callback_data="back_to_menu"))
        
        await call.message.edit_text(
            "Способи пiдтримки:\nTelegram Stars - миттєве поповнення\nDonationAlerts/Monobank - прямi донати",
            reply_markup=builder.as_markup()
        )
        await call.answer()

    @dp.callback_query(F.data == "show_monobank_card")
    async def show_monobank_card(call: types.CallbackQuery):
        builder = InlineKeyboardBuilder()
        builder.row(types.InlineKeyboardButton(text="Назад", callback_data="donation_menu"))
        await call.message.edit_text(
            f"Monobank картка:\n<code>{MONOBANK_CARD}</code>",
            reply_markup=builder.as_markup(),
            parse_mode="HTML"
        )
        await call.answer()

    @dp.callback_query(F.data == "back_to_menu")
    async def back_to_menu(call: types.CallbackQuery):
        await call.message.edit_text("Меню:", reply_markup=get_main_menu())
        await call.answer()

    # ========== ОПЛАТА TELEGRAM STARS ==========
    @dp.callback_query(F.data == "top_up_stars")
    async def top_up_stars(call: types.CallbackQuery):
        await call.message.answer_invoice(
            title="Поповнення балансу",
            description="Купити 100 зiрок",
            prices=[LabeledPrice(label="100 зiрок", amount=100)],
            payload="topup_100_stars",
            currency="XTR",
            provider_token=""
        )
        await call.answer()

    @dp.pre_checkout_query()
    async def process_pre_checkout(query: PreCheckoutQuery):
        await query.answer(ok=True)

    @dp.message(F.successful_payment)
    async def on_successful_payment(message: types.Message):
        await db.add_stars(str(message.from_user.id), 100)
        await message.answer("Оплата успiшна! +100 зiрок на баланс.")

    # ========== ОСНОВНИЙ ЧАТ ==========
    @dp.message()
    async def chat_handler(m: types.Message):
        if not m.text:
            return
        
        u_id = str(m.from_user.id)
        user = await db.get_user(u_id)
        if not user:
            await m.answer("Напиши /start")
            return
        
        await bot.send_chat_action(m.chat.id, "typing")
        await asyncio.sleep(0.5)
        
        response = await get_ai_response(u_id, m.text, db, ai_service)
        
        is_private = user.get('private_until', 0) > time.time()
        voices_left = user.get('voice_limit', 0)
        
        if is_private and voices_left > 0 and len(response) > 35 and random.random() < 0.55:
            await bot.send_chat_action(m.chat.id, "record_voice")
            voice_bytes = await ai_service.generate_voice(response)
            
            if voice_bytes:
                voice = BufferedInputFile(voice_bytes, filename="voice.mp3")
                await m.answer_voice(voice)
                await db.update_user(u_id, voice_limit=voices_left - 1)
            else:
                await m.answer(response)
        else:
            await m.answer(response)