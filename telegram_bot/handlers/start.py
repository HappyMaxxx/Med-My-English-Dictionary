from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart
import aiohttp
import logging

router = Router()

@router.message(CommandStart())
async def start_handler(message: Message):
    args = message.text.split()[1:]
    chat_id = message.chat.id

    if args:
        token = args[0]

        async with aiohttp.ClientSession() as session:
            payload = {
                "token": token,
                "chat_id": chat_id
            }

            try:
                async with session.post(
                    "http://web:8000/api/v1/link-telegram/",
                    json=payload
                ) as resp:
                    
                    response_text = await resp.text()
                    
                    if resp.status == 200:
                        try:
                            data = await resp.json(content_type=None)
                            
                            await message.answer(
                                f"Успіх! Ваш акаунт прив'язано до користувача {data.get('username', 'Unknown')}."
                            )
                        except Exception as e:
                            logging.error(f"Server returned 200 but content is not JSON: {response_text}")
                            await message.answer("Помилка сервера: отримано некоректні дані.")
                    else:
                        logging.error(f"Error {resp.status}: {response_text}")
                        await message.answer(
                            "Помилка прив'язки. Спробуйте згенерувати посилання знову."
                        )
            except Exception as e:
                logging.exception("Connection error")
                await message.answer("Не вдалося з'єднатися з сервером.")
    else:
        await message.answer(
            "Привіт! Щоб підключити бота, перейдіть у налаштування профілю на сайті."
        )