from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import aiohttp

from services.redis_storage import get_user_token

router = Router()

API_BASE = "http://web:8000/api/v1/"

@router.message(Command("unlink_telegram"))
async def start_handler(message: Message):
    chat_id = message.chat.id
    args = message.text.split()[1:]
    token = await get_user_token(chat_id)

    if not token:
        raise Exception("Користувач не прив’язав токен через /start")

    headers = {"Authorization": f"Token {token}"}

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{API_BASE}unlink-telegram/", headers=headers) as resp:
            if resp.ok:
                data = await resp.json()
                username = data.get("username", "користувач")
                
                text = (
                    f"✅ <b>{username}</b>, ваш акаунт успішно відключено!\n\n"
                    "Синхронізацію зі словником припинено. Щоб підключитися знову, "
                    "використовуйте нове посилання з особистого кабінету."
                )
                
                await message.answer(text, parse_mode="HTML")
            else:
                text = await resp.text()
                raise Exception(f"API error {resp.status}: {text}")