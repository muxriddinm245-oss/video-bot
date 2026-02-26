from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart

import database as db
from config import ADMIN_ID
from keyboards.user_kb import (
    main_menu_kb, catalog_kb, course_detail_kb,
    back_to_menu_kb, my_courses_kb
)

router = Router()

WELCOME_TEXT = (
    "👋 Salom, <b>{name}</b>!\n\n"
    "🎬 <b>Video Darsliklar Do'koniga xush kelibsiz!</b>\n\n"
    "📚 Bu botda dasturlash bo'yicha professional video kurslar sotiladi.\n"
    "💳 To'lov — karta orqali so'mda\n"
    "🔓 To'lovdan so'ng video darhol yuboriladi\n"
    "♾️ Bir marta sotib oling — doim ko'ring!\n\n"
    "👇 Quyidagi menyudan boshlang:"
)


@router.message(CommandStart())
async def cmd_start(message: Message):
    is_new = not await db.user_exists(message.from_user.id)
    await db.add_user(message.from_user.id, message.from_user.username, message.from_user.full_name)

    await message.answer(
        WELCOME_TEXT.format(name=message.from_user.first_name),
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )

    # Notify admin about new user
    if is_new:
        try:
            await message.bot.send_message(
                ADMIN_ID,
                f"🆕 <b>Yangi foydalanuvchi!</b>\n\n"
                f"👤 {message.from_user.full_name}\n"
                f"🔗 @{message.from_user.username or 'username yoq'}\n"
                f"🆔 <code>{message.from_user.id}</code>",
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🏠 <b>Bosh menyu</b>\n\nQuyidagilardan birini tanlang:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "catalog")
async def show_catalog(callback: CallbackQuery):
    courses = await db.get_all_courses()
    if not courses:
        await callback.answer("Hozircha kurslar mavjud emas! Tez orada qo'shiladi 👨‍💻", show_alert=True)
        return
    await callback.message.edit_text(
        f"📚 <b>Kurslar katalogi</b>  ({len(courses)} ta kurs)\n\n"
        "Qiziqtirgan kursni tanlang 👇",
        reply_markup=catalog_kb(courses),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("course_"))
async def show_course(callback: CallbackQuery):
    course_id = int(callback.data.split("_")[1])
    course = await db.get_course(course_id)
    if not course:
        await callback.answer("Kurs topilmadi!", show_alert=True)
        return

    purchased = await db.has_purchased(callback.from_user.id, course_id)
    price_str = f"{course['price_uzs']:,} so'm"
    status = "✅ <b>Sotib olingan</b> — video ko'rish uchun tugmani bosing" if purchased else f"💰 Narx: <b>{price_str}</b>"

    text = (
        f"🎬 <b>{course['title']}</b>\n\n"
        f"📝 {course['description']}\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{status}"
    )

    if course['thumbnail_file_id'] and not purchased:
        try:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=course['thumbnail_file_id'],
                caption=text,
                reply_markup=course_detail_kb(course_id, purchased),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        except Exception:
            pass

    await callback.message.edit_text(
        text,
        reply_markup=course_detail_kb(course_id, purchased),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("watch_"))
async def watch_video(callback: CallbackQuery):
    course_id = int(callback.data.split("_")[1])
    purchased = await db.has_purchased(callback.from_user.id, course_id)
    if not purchased:
        await callback.answer("❌ Avval kursni sotib oling!", show_alert=True)
        return

    course = await db.get_course(course_id)
    if not course or not course['video_file_id']:
        await callback.answer("Video hali yuklanmagan, tez orada qo'shiladi!", show_alert=True)
        return

    await callback.message.answer_video(
        video=course['video_file_id'],
        caption=(
            f"🎬 <b>{course['title']}</b>\n\n"
            f"✅ Bu kurs sizga tegishli — istalgan vaqt ko'rishingiz mumkin!\n\n"
            f"🚀 O'qishingizga muvaffaqiyat!"
        ),
        parse_mode="HTML"
    )
    await callback.answer()


@router.callback_query(F.data == "my_courses")
async def my_courses(callback: CallbackQuery):
    courses = await db.get_user_purchases(callback.from_user.id)
    if not courses:
        await callback.message.edit_text(
            "📭 <b>Siz hali birorta kurs sotib olmadingiz.</b>\n\n"
            "Katalogdan o'zingizga mos kursni tanlang va boshlang! 🚀",
            reply_markup=back_to_menu_kb(),
            parse_mode="HTML"
        )
        return

    await callback.message.edit_text(
        f"🎓 <b>Mening kurslarim</b>  ({len(courses)} ta)\n\n"
        "Ko'rmoqchi bo'lgan kursni tanlang 👇",
        reply_markup=my_courses_kb(courses),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "contact_admin")
async def contact_admin(callback: CallbackQuery):
    await callback.message.edit_text(
        "📞 <b>Admin bilan bog'lanish</b>\n\n"
        "Savol yoki muammolaringiz bo'lsa, adminga yozing:\n\n"
        "👉 @admin_username_bu_yerga\n\n"
        "⏱ Javob vaqti: 24 soat ichida",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "about")
async def about_bot(callback: CallbackQuery):
    await callback.message.edit_text(
        "ℹ️ <b>Bot haqida</b>\n\n"
        "Bu bot orqali dasturlash bo'yicha sifatli video darsliklar sotib olishingiz mumkin.\n\n"
        "💳 <b>To'lov:</b> Karta orqali so'mda\n"
        "⚡ <b>Tezlik:</b> To'lov tasdiqlangach darhol video yuboriladi\n"
        "♾️ <b>Muddatsiz:</b> Bir marta sotib oling, doim ko'ring\n"
        "🔒 <b>Xavfsiz:</b> Barcha to'lovlar admin tomonidan tekshiriladi\n\n"
        "📩 Savollar uchun: /start → Admin bilan bog'lanish",
        reply_markup=back_to_menu_kb(),
        parse_mode="HTML"
    )
