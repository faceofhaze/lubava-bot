# bot.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import TOKEN
from database import Database
from ai_service import AIService
from handlers import register_handlers
from utils import has_video_files

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    # Ініціалізація
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    db = Database()
    ai_service = AIService()
    
    # Підключення до БД (одне з'єднання на весь час)
    await db.init()
    
    # Реєстрація обробників
    register_handlers(dp, bot, db, ai_service)
    
    # Перевірка відео
    hello = has_video_files("videos")
    kiss = has_video_files("video_notes")
    
    print("=" * 50)
    print("Любава v6.0 ЗАПУЩЕНА!")
    print(f"Вiдео-привiтання: {'Є' if hello else 'Немає'}")
    print(f"Вiдео-подяка: {'Є' if kiss else 'Немає'}")
    print("=" * 50)
    
    try:
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
