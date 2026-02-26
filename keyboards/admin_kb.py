from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def admin_main_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="➕ Kurs qo'shish"), KeyboardButton(text="📋 Kurslar ro'yxati")],
        [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Xabar yuborish")],
        [KeyboardButton(text="⏳ Kutayotgan to'lovlar")],
    ], resize_keyboard=True)


def cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="❌ Bekor qilish")]
    ], resize_keyboard=True)


def course_manage_kb(course_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ O'chirish", callback_data=f"del_course_{course_id}")],
    ])


def confirm_delete_kb(course_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, o'chir", callback_data=f"confirm_del_{course_id}"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="cancel_delete"),
        ]
    ])


def payment_action_kb(payment_id: int, user_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"approve_{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"reject_{payment_id}"),
        ],
        [InlineKeyboardButton(text="💬 Xabar yuborish", callback_data=f"msg_user_{user_id}_{payment_id}")]
    ])
