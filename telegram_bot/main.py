import os
import django
import sys
from decouple import config
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message

import asyncio
import logging
from aiogram.fsm.storage.redis import RedisStorage

sys.path.append("/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mad.settings")
django.setup()

os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = config('BOT_TOKEN', default=None)
if not BOT_TOKEN:
    logger.error("BOT_TOKEN is not set in the .env file. Exiting...")
    sys.exit(1) 

bot = Bot(token=BOT_TOKEN)
storage = RedisStorage.from_url("redis://redis:6379/0")
dp = Dispatcher(storage=storage)

commands = [
    types.BotCommand(command="start", description="Get started"),
    types.BotCommand(command="help", description="Get help"),
]

async def on_startup():
    await bot.set_my_commands(commands)

@dp.message()
async def echo_handler(message: Message):
    await message.answer(message.text)

async def main():
    try:
        await on_startup()
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"An error occurred while running the bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())