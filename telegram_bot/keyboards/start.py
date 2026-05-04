from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

new_word_on_start_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Додати нове слово", callback_data="new_word")]
    ]
)