# database.py
import json
import logging
from typing import Dict, Any, Optional
import aiosqlite

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = "lyubava.db"):
        self.db_path = db_path
        self._db = None

    async def init(self):
        """Єдине з'єднання на весь час роботи бота"""
        self._db = await aiosqlite.connect(self.db_path)
        self._db.row_factory = aiosqlite.Row
        
        await self._db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                u_id TEXT PRIMARY KEY,
                stars INTEGER DEFAULT 100,
                reputation INTEGER DEFAULT 500,
                private_until INTEGER DEFAULT 0,
                voice_limit INTEGER DEFAULT 0,
                age INTEGER DEFAULT 0,
                gender TEXT DEFAULT '',
                name TEXT DEFAULT '',
                long_term_memory TEXT DEFAULT '{}',
                history TEXT DEFAULT '[]',
                has_seen_welcome BOOLEAN DEFAULT 0
            )
        """)
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.commit()
        logger.info("База даних ініціалізована (постійне з'єднання)")

    async def get_user(self, u_id: str) -> Optional[Dict]:
        async with self._db.execute("SELECT * FROM users WHERE u_id = ?", (u_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data['history'] = json.loads(data['history'])
                data['long_term_memory'] = json.loads(data['long_term_memory'])
                data['has_seen_welcome'] = bool(data['has_seen_welcome'])
                return data
            return None

    async def update_user(self, u_id: str, **kwargs):
        if 'history' in kwargs:
            history = kwargs['history']
            if len(history) > 30:
                history = history[-30:]
            kwargs['history'] = json.dumps(history, ensure_ascii=False)
        if 'long_term_memory' in kwargs:
            kwargs['long_term_memory'] = json.dumps(kwargs['long_term_memory'], ensure_ascii=False)
        
        keys = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [u_id]
        await self._db.execute(f"UPDATE users SET {keys} WHERE u_id = ?", values)
        await self._db.commit()

    async def create_user(self, u_id: str):
        await self._db.execute("INSERT OR IGNORE INTO users (u_id) VALUES (?)", (u_id,))
        await self._db.commit()

    async def add_stars(self, u_id: str, amount: int):
        await self._db.execute("UPDATE users SET stars = stars + ? WHERE u_id = ?", (amount, u_id))
        await self._db.commit()

    async def remove_stars(self, u_id: str, amount: int):
        await self._db.execute("UPDATE users SET stars = stars - ? WHERE u_id = ?", (amount, u_id))
        await self._db.commit()

    async def update_reputation(self, u_id: str, delta: int):
        await self._db.execute("UPDATE users SET reputation = reputation + ? WHERE u_id = ?", (delta, u_id))
        await self._db.commit()

    async def save_user_info(self, u_id: str, name: str = None, age: int = None, gender: str = None):
        updates = {}
        if name:
            updates['name'] = name
        if age:
            updates['age'] = age
        if gender:
            updates['gender'] = gender
        if updates:
            await self.update_user(u_id, **updates)
            logger.info(f"Збережено iнфо для {u_id}: {updates}")

    async def close(self):
        if self._db:
            await self._db.close()