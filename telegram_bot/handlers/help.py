from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

router = Router()

@router.message(Command("help"))
async def help_handler(message: Message):
    await message.answer("Це розділ допомоги.")