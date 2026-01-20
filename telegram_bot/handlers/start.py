from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
import aiohttp
import logging

from services.redis_storage import store_user_token

router = Router()

API_BASE = "http://web:8000/api/v1/"

@router.message(CommandStart())
async def start_handler(message: Message):
    chat_id = message.chat.id
    args = message.text.split()[1:]

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API_BASE}telegram-status/?chat_id={chat_id}") as resp:
            data = await resp.json()
            if data.get("linked"):
                if not args:
                    async with session.get(f"{API_BASE}telegram-token/?chat_id={chat_id}") as token_resp:
                        token_data = await token_resp.json()
                        token = token_data.get("token")
                        if token:
                            await store_user_token(chat_id, token)
                        else:
                            logging.warning(f"No token returned for chat_id {chat_id}")

                text = f"Привіт, {data['username']} 👋\nДодамо нове слово?"
                await message.answer(text)
                return

        if args:
            token = args[0]
            payload = {"token": token, "chat_id": chat_id}

            try:
                async with session.post(f"{API_BASE}link-telegram/", json=payload) as resp:
                    response_text = await resp.text()
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        await store_user_token(chat_id, token)
                        await message.answer(
                            f"Успіх! Ваш акаунт прив'язано до користувача {data.get('username', 'Unknown')}."
                        )
                    else:
                        logging.error(f"Error {resp.status}: {response_text}")
                        await message.answer(
                            "Помилка прив'язки. Спробуйте згенерувати посилання знову."
                        )
            except Exception:
                logging.exception("Connection error")
                await message.answer("Не вдалося з'єднатися з сервером.")
        else:
            await message.answer(
                "Привіт! Щоб підключити бота, перейдіть у налаштування профілю на сайті і натисніть 'Прив'язати Telegram'."
            )
