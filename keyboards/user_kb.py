from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)


def main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 Kurslar katalogi", callback_data="catalog")],
        [InlineKeyboardButton(text="🎓 Mening kurslarim", callback_data="my_courses")],
        [InlineKeyboardButton(text="📞 Admin bilan bog'lanish", callback_data="contact_admin")],
        [InlineKeyboardButton(text="ℹ️ Bot haqida", callback_data="about")],
    ])


def catalog_kb(courses):
    buttons = []
    for course in courses:
        price = f"{course['price_uzs']:,}"
        buttons.append([
            InlineKeyboardButton(
                text=f"🎬 {course['title']}  |  💰 {price} so'm",
                callback_data=f"course_{course['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def course_detail_kb(course_id: int, purchased: bool):
    buttons = []
    if purchased:
        buttons.append([InlineKeyboardButton(text="▶️ Videoni ko'rish", callback_data=f"watch_{course_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="💳 Karta orqali sotib olish", callback_data=f"buy_{course_id}")])
    buttons.append([InlineKeyboardButton(text="◀️ Katalogga qaytish", callback_data="catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Katalogga qaytish", callback_data="catalog")],
        [InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")],
    ])


def my_courses_kb(courses):
    buttons = []
    for course in courses:
        buttons.append([
            InlineKeyboardButton(
                text=f"▶️ {course['title']}",
                callback_data=f"watch_{course['id']}"
            )
        ])
    buttons.append([InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_payment_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_payment")]
    ])
