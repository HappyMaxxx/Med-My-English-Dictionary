import aiohttp
from services.redis_storage import get_user_token

API_URL = "http://web:8000/api/v1/words/"

async def add_word_api(chat_id, english, translation, example=None):
    token = await get_user_token(chat_id)
    if not token:
        raise Exception("Користувач не прив’язав токен через /start")

    payload = {
        "word": english,
        "translation": translation,
        "example": example
    }
    headers = {"Authorization": f"Token {token}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload, headers=headers) as resp:
            if resp.status == 201:
                return await resp.json()
            else:
                text = await resp.text()
                raise Exception(f"API error {resp.status}: {text}")
