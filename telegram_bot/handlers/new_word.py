from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states.new_word import NewWordState
from keyboards.new_word import skip_example_kb, confirm_kb
from services.dictionary import add_word_api

router = Router()

async def start_new_word_process(message_or_callback, state: FSMContext):
    await state.clear()
    if isinstance(message_or_callback, Message):
        await message_or_callback.answer("Введи слово англійською 🇬🇧")
    elif isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer("Введи слово англійською 🇬🇧")
        await message_or_callback.answer()
    await state.set_state(NewWordState.english)

@router.message(Command("new_word"))
async def new_word_start(message: Message, state: FSMContext):
    await start_new_word_process(message, state)

@router.callback_query(lambda c: c.data == "new_word")
async def new_word_callback(callback: CallbackQuery, state: FSMContext):
    await start_new_word_process(callback, state)

@router.message(NewWordState.english)
async def get_english(message: Message, state: FSMContext):
    await state.update_data(english=message.text.strip())
    await message.answer("Тепер введи переклад 🇺🇦")
    await state.set_state(NewWordState.translation)

@router.message(NewWordState.translation)
async def get_translation(message: Message, state: FSMContext):
    await state.update_data(translation=message.text.strip())
    await message.answer(
        "Введи приклад використання ✍️\nАбо натисни кнопку нижче",
        reply_markup=skip_example_kb
    )
    await state.set_state(NewWordState.example)

@router.message(NewWordState.example)
async def get_example(message: Message, state: FSMContext):
    await state.update_data(example=message.text.strip())
    await show_confirm(message, state)

@router.callback_query(F.data == "skip_example", NewWordState.example)
async def skip_example(callback: CallbackQuery, state: FSMContext):
    await state.update_data(example="")
    await callback.message.edit_reply_markup(reply_markup=None)
    await show_confirm(callback.message, state)

async def show_confirm(message: Message, state: FSMContext):
    data = await state.get_data()
    text = (
        "🔍 <b>Перевір, чи все правильно:</b>\n\n"
        f"🇬🇧 <b>Слово:</b> {data['english']}\n"
        f"🇺🇦 <b>Переклад:</b> {data['translation']}\n"
        f"✍️ <b>Приклад:</b> {data.get('example') or '—'}"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=confirm_kb)
    await state.set_state(NewWordState.confirm)

@router.callback_query(F.data == "confirm_add", NewWordState.confirm)
async def confirm_add(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        await add_word_api(
            chat_id=callback.from_user.id,
            english=data["english"],
            translation=data["translation"],
            example=data.get("example")
        )
        await callback.message.edit_text("✅ Слово додано до словника!")
    except Exception as e:
        await callback.message.edit_text(f"❌ Помилка: {e}")
    finally:
        await state.clear()

@router.callback_query(F.data == "cancel_add")
async def cancel_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Додавання скасовано")
