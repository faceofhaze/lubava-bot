# ai_service.py
import asyncio
import logging
import time
import random
import os
import re
import json
from typing import Optional, List, Dict
import httpx
from groq import Groq
from config import GROQ_KEY, EL_KEY, VOICE_ID

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_KEY)

    async def groq_completion(self, messages: list, temperature: float = 0.95, max_tokens: int = 500) -> Optional[str]:
        """Асинхронний виклик Groq через to_thread"""
        try:
            result = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=["\nКористувач:", "\nUser:", "User:", "Користувач:"]
            )
            return result.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq помилка: {e}")
            return None

    async def extract_user_info(self, user_text: str) -> Dict:
        """Витягує ім'я, вік, стать з повідомлення"""
        prompt = f"""
        Проаналізуй повідомлення та витягни iнформацiю.
        Повiдомлення: "{user_text}"
        
        Формат (ТIЛЬКИ JSON): {{"name": "", "age": 0, "gender": ""}}
        """
        
        result = await self.groq_completion(
            [{"role": "system", "content": prompt}],
            temperature=0.1,
            max_tokens=100
        )
        
        if result:
            result = re.sub(r'```json\n?|```', '', result).strip()
            try:
                return json.loads(result)
            except:
                pass
        return {"name": "", "age": 0, "gender": ""}

    async def generate_voice(self, text: str) -> Optional[bytes]:
        """Генерує голос, повертає bytes (без збереження на диск)"""
        if not EL_KEY:
            return None
        
        if len(text) > 500:
            text = text[:500]
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": EL_KEY
        }
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.4,
                "similarity_boost": 0.8,
                "style": 0.45,
                "use_speaker_boost": True
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, headers=headers, timeout=30)
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"ElevenLabs помилка: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"ElevenLabs Error: {e}")
            return None