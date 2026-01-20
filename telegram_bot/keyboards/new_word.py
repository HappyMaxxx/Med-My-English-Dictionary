from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

skip_example_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➡️ Пропустити приклад", callback_data="skip_example")]
    ]
)

confirm_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Додати", callback_data="confirm_add"),
            InlineKeyboardButton(text="❌ Скасувати", callback_data="cancel_add"),
        ]
    ]
)