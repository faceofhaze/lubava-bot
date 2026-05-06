# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не знайдено!")

# Groq
GROQ_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_KEY:
    raise ValueError("GROQ_API_KEY не знайдено!")

# ElevenLabs
EL_KEY = os.getenv("ELEVENLABS_API_KEY")
VOICE_ID = os.getenv("VOICE_ID", "21m00Tcm4TlvDq8ikWAM")

# Донати
DONATION_ALERT_URL = os.getenv("DONATION_ALERT_URL", "")
MONOBANK_CARD = os.getenv("MONOBANK_CARD", "")
MONOBANK_URL = os.getenv("MONOBANK_URL", "")

# Налаштування
MAX_HISTORY_LENGTH = 30
MEMORY_SIZE = 15
MEMORY_EXPIRE = 300
REPUTATION_INCREMENT = 5

# Ціни
PRICES = {
    "private_30min": 30,
    "private_60min": 50,
    "kiss": 50,
}

PRIVATE_BONUSES = {
    30: {"minutes": 30, "voice_limit": 15, "title": "Приват 30 хв"},
    50: {"minutes": 60, "voice_limit": 30, "title": "Приват 60 хв"},
}

RELATIONSHIP_LEVELS = {
    1: {"name": "Знайомі", "min_rep": 0, "bonus": "Базовi фото", "style": "стримано"},
    2: {"name": "Друзі", "min_rep": 200, "bonus": "Голосовi зi знижкою", "style": "тепло"},
    3: {"name": "Близькi друзi", "min_rep": 500, "bonus": "Вiдвертi фото", "style": "флiрт"},
    4: {"name": "Коханцi", "min_rep": 800, "bonus": "Ексклюзив", "style": "пристрасно"},
    5: {"name": "Спорiдненi душi", "min_rep": 1000, "bonus": "Все без обмежень", "style": "абсолютна вiдвертiсть"},
}