# utils.py
import os
import random
import time
from typing import Dict, Any, Optional
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton

from config import RELATIONSHIP_LEVELS, PRICES, PRIVATE_BONUSES

def get_level_info(rep: int):
    for lvl, info in sorted(RELATIONSHIP_LEVELS.items(), reverse=True):
        if rep >= info["min_rep"]:
            return lvl, info
    return 1, RELATIONSHIP_LEVELS[1]

def get_discounted_price(base_price: int, rep: int) -> int:
    if rep >= 1000:
        return int(base_price * 0.5)
    elif rep >= 800:
        return int(base_price * 0.7)
    elif rep >= 500:
        return int(base_price * 0.8)
    elif rep >= 200:
        return int(base_price * 0.9)
    return base_price

def detect_user_type(age: int, gender: str, reputation: int) -> Dict[str, str]:
    if 0 < age < 14:
        style = "Старша сестра: турботлива, грайлива, без флiрту."
    elif 14 <= age < 18:
        style = "Молодша подруга: дружня, злегка флiртує."
    elif 18 <= age < 30:
        style = "Подруга/Коханка: флiрт, жарти, енергiйнiсть."
    elif 30 <= age < 50:
        style = "Досвiдчена жiнка: розумна, чуттєва."
    elif age >= 50:
        style = "Турботлива супутниця: повага, теплота."
    else:
        style = "Нейтральний: ввiчлива, вiдкрита."

    if gender == "male":
        gender_style = "Спiлкуйся як з чоловiком"
    elif gender == "female":
        gender_style = "Спiлкуйся як з подругою"
    else:
        gender_style = "Будь ввiчливою"

    return {"style": style, "gender_style": gender_style}

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Статус", callback_data="status"))
    builder.row(InlineKeyboardButton(text="Про мене", callback_data="about_me"))
    builder.row(InlineKeyboardButton(text="Очистити iсторiю", callback_data="clear_history"))
    builder.row(InlineKeyboardButton(text="Приват 30 хв (30)", callback_data="buy_private_30"))
    builder.row(InlineKeyboardButton(text="Приват 60 хв (50)", callback_data="buy_private_60"))
    builder.row(InlineKeyboardButton(text="Подякувати (50)", callback_data="donate_kiss"))
    builder.row(InlineKeyboardButton(text="Пiдтримати", callback_data="donation_menu"))
    return builder.as_markup()

def has_video_files(folder: str) -> bool:
    if not os.path.exists(folder):
        return False
    videos = [f for f in os.listdir(folder) if f.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))]
    return len(videos) > 0

async def send_random_video(message, folder: str, caption: str) -> bool:
    if not has_video_files(folder):
        return False
    videos = [f for f in os.listdir(folder) if f.endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm'))]
    video_name = random.choice(videos)
    video_path = os.path.join(folder, video_name)
    try:
        video = FSInputFile(video_path)
        await message.answer_video(video, caption=caption, parse_mode="Markdown")
        return True
    except Exception as e:
        return False

async def send_kiss_video(message):
    return await send_random_video(message, "video_notes", "")

async def get_ai_response(u_id: str, user_text: str, db, ai_service):
    user = await db.get_user(u_id)
    if not user:
        return "Напиши /start"
    
    history = user['history'][-12:]
    is_private = user.get('private_until', 0) > time.time()
    age = user.get('age', 0)
    gender = user.get('gender', '')
    user_name = user.get('name', '')
    voices_left = user.get('voice_limit', 0)
    
    # Нарахування зiрок (10% шанс)
    if random.random() < 0.1:
        await db.add_stars(u_id, 1)
    
    known_info = ""
    if age > 0:
        known_info += f"- Тобi {age} рокiв\n"
    if gender:
        known_info += f"- Ти {'хлопець' if gender == 'male' else 'дiвчина'}\n"
    if user_name:
        known_info += f"- Тебе звати {user_name}\n"
    
    if is_private:
        system_instr = f"""
        Ти Любава, 30 рокiв. Ти в ПРИВАТНОМУ режимi.
        Мова: українська.
        {known_info}
        У тебе залишилось {voices_left} голосових.
        Ти не ШI, не бот. Ти жива жiнка. Флiртуй, але не здавайся одразу.
        """
    else:
        user_type = detect_user_type(age, gender, user.get('reputation', 500))
        system_instr = f"""
        Ти Любава, 30 рокiв. Мова: українська.
        {known_info}
        Стиль: {user_type['style']}
        Не кажи "я ШI". Не вiтайся.
        """
    
    messages = [{"role": "system", "content": system_instr}]
    for h in history:
        messages.append({"role": "user" if h['role'] == 'u' else "assistant", "content": h['txt']})
    messages.append({"role": "user", "content": user_text})
    
    response = await ai_service.groq_completion(messages)
    
    if response:
        history.append({"role": "u", "txt": user_text})
        history.append({"role": "a", "txt": response})
        await db.update_user(u_id, history=history)
        
        # Асинхронне витягування iнформацiї (не блокує вiдповiдь)
        asyncio.create_task(extract_and_save_info(u_id, user_text, db, ai_service))
        
        return response
    else:
        return "Вибач, повтори ще раз..."

async def extract_and_save_info(u_id: str, user_text: str, db, ai_service):
    """Фоновий аналіз даних користувача"""
    info = await ai_service.extract_user_info(user_text)
    if info.get('name') or info.get('age') or info.get('gender'):
        await db.save_user_info(u_id, 
            name=info.get('name'), 
            age=info.get('age'), 
            gender=info.get('gender'))