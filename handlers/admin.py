from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_ID
from keyboards.admin_kb import admin_main_kb, cancel_kb, course_manage_kb, confirm_delete_kb

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID


# ── FSM States ────────────────────────────────────────────────────────────────

class AddCourse(StatesGroup):
    title = State()
    description = State()
    price = State()
    video = State()


class BroadcastState(StatesGroup):
    waiting_message = State()


# ── Admin Panel ───────────────────────────────────────────────────────────────

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q!")
        return
    users, courses, purchases, total_uzs, pending = await db.get_stats()
    await message.answer(
        f"👑 <b>Admin Panel</b>\n\n"
        f"📊 Bugungi holat:\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"🎬 Kurslar: <b>{courses}</b>\n"
        f"💳 Jami sotuvlar: <b>{purchases}</b>\n"
        f"💵 Tushum: <b>{total_uzs:,} so'm</b>\n"
        f"⏳ Kutayotgan to'lovlar: <b>{pending}</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


# ── Add Course Flow ───────────────────────────────────────────────────────────

@router.message(F.text == "➕ Kurs qo'shish")
async def add_course_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(AddCourse.title)
    await message.answer(
        "📝 <b>Yangi kurs qo'shish</b>\n\n"
        "1-qadam: Kurs <b>nomini</b> kiriting:",
        reply_markup=cancel_kb(),
        parse_mode="HTML"
    )


@router.message(AddCourse.title)
async def add_course_title(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_kb())
        return
    await state.update_data(title=message.text)
    await state.set_state(AddCourse.description)
    await message.answer("2-qadam: Kurs <b>tavsifini</b> kiriting (nima o'rgatadi, kimlar uchun):", parse_mode="HTML")


@router.message(AddCourse.description)
async def add_course_description(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_kb())
        return
    await state.update_data(description=message.text)
    await state.set_state(AddCourse.price)
    await message.answer("3-qadam: <b>Narxini</b> so'mda kiriting:\n(Masalan: 50000)", parse_mode="HTML")


@router.message(AddCourse.price)
async def add_course_price(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_kb())
        return
    price_str = message.text.replace(" ", "").replace(",", "")
    if not price_str.isdigit() or int(price_str) < 1000:
        await message.answer("❌ Kamida 1000 so'm bo'lishi kerak. Qaytadan kiriting:")
        return
    await state.update_data(price=int(price_str))
    await state.set_state(AddCourse.video)
    await message.answer("4-qadam: 🎬 <b>Video faylni</b> yuboring:", parse_mode="HTML")


@router.message(AddCourse.video, F.video)
async def add_course_video(message: Message, state: FSMContext):
    data = await state.get_data()
    video_file_id = message.video.file_id
    thumbnail_file_id = message.video.thumbnail.file_id if message.video.thumbnail else None

    course_id = await db.add_course(
        title=data['title'],
        description=data['description'],
        price_uzs=data['price'],
        video_file_id=video_file_id,
        thumbnail_file_id=thumbnail_file_id
    )
    await state.clear()
    await message.answer(
        f"✅ <b>Kurs muvaffaqiyatli qo'shildi!</b>\n\n"
        f"🆔 ID: {course_id}\n"
        f"📌 Nom: <b>{data['title']}</b>\n"
        f"💰 Narx: <b>{data['price']:,} so'm</b>\n\n"
        f"Kurs endi foydalanuvchilarga ko'rinadi 🚀",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )


@router.message(AddCourse.video)
async def add_course_video_wrong(message: Message):
    if message.text == "❌ Bekor qilish":
        return
    await message.answer("❌ Iltimos, faqat video fayl yuboring!")


# ── Course List ───────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Kurslar ro'yxati")
async def list_courses(message: Message):
    if not is_admin(message.from_user.id):
        return
    courses = await db.get_all_courses()
    if not courses:
        await message.answer("📭 Hozircha kurslar yo'q. ➕ Kurs qo'shish tugmasini bosing.")
        return
    for course in courses:
        text = (
            f"🆔 <b>ID: {course['id']}</b>  |  💰 {course['price_uzs']:,} so'm\n"
            f"📌 <b>{course['title']}</b>\n"
            f"📝 {course['description']}"
        )
        await message.answer(text, reply_markup=course_manage_kb(course['id']), parse_mode="HTML")


@router.callback_query(F.data.startswith("del_course_"))
async def delete_course_prompt(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    course_id = int(callback.data.split("_")[2])
    course = await db.get_course(course_id)
    await callback.message.edit_text(
        f"🗑️ <b>O'chirishni tasdiqlaysizmi?</b>\n\n<b>{course['title']}</b>",
        reply_markup=confirm_delete_kb(course_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_del_"))
async def confirm_delete(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    course_id = int(callback.data.split("_")[2])
    await db.delete_course(course_id)
    await callback.message.edit_text("✅ Kurs o'chirildi!")


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    await callback.message.edit_text("❌ Bekor qilindi.")


# ── Stats ─────────────────────────────────────────────────────────────────────

@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message):
    if not is_admin(message.from_user.id):
        return
    users, courses, purchases, total_uzs, pending = await db.get_stats()
    await message.answer(
        f"📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{users}</b>\n"
        f"🎬 Faol kurslar: <b>{courses}</b>\n"
        f"💳 Jami sotuvlar: <b>{purchases}</b>\n"
        f"💵 Jami tushum: <b>{total_uzs:,} so'm</b>\n"
        f"⏳ Kutayotgan to'lovlar: <b>{pending}</b>",
        parse_mode="HTML"
    )


# ── Pending Payments ──────────────────────────────────────────────────────────

@router.message(F.text == "⏳ Kutayotgan to'lovlar")
async def show_pending(message: Message):
    if not is_admin(message.from_user.id):
        return
    pendings = await db.get_pending_payments()
    if not pendings:
        await message.answer("✅ Hozircha kutayotgan to'lov yo'q!")
        return
    for p in pendings:
        course = await db.get_course(p['course_id'])
        from keyboards.admin_kb import payment_action_kb
        await message.answer_photo(
            photo=p['screenshot_file_id'],
            caption=(
                f"⏳ <b>Kutayotgan to'lov #{p['id']}</b>\n\n"
                f"👤 Foydalanuvchi ID: <code>{p['user_id']}</code>\n"
                f"🎬 Kurs: <b>{course['title'] if course else '?'}</b>\n"
                f"💵 Narx: <b>{course['price_uzs']:,} so'm</b>\n"
                f"🕐 Vaqt: {p['created_at']}"
            ),
            reply_markup=payment_action_kb(p['id'], p['user_id']),
            parse_mode="HTML"
        )


# ── Broadcast ─────────────────────────────────────────────────────────────────

@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.set_state(BroadcastState.waiting_message)
    await message.answer(
        "📢 Barcha foydalanuvchilarga yubormoqchi bo'lgan xabarni yozing\n"
        "(matn, rasm, video — istalgan format):",
        reply_markup=cancel_kb()
    )


@router.message(BroadcastState.waiting_message)
async def broadcast_send(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=admin_main_kb())
        return

    await state.clear()
    user_ids = await db.get_all_user_ids()
    success = 0
    failed = 0
    status_msg = await message.answer(f"📤 Yuborilmoqda... 0/{len(user_ids)}")

    for i, uid in enumerate(user_ids):
        try:
            await message.bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
        except Exception:
            failed += 1
        # Update progress every 10 users
        if (i + 1) % 10 == 0:
            try:
                await status_msg.edit_text(f"📤 Yuborilmoqda... {i+1}/{len(user_ids)}")
            except Exception:
                pass

    await status_msg.edit_text(
        f"✅ <b>Xabar yuborildi!</b>\n\n"
        f"✅ Muvaffaqiyatli: {success}\n"
        f"❌ Yuborilmadi: {failed}\n"
        f"📊 Jami: {len(user_ids)}",
        parse_mode="HTML"
    )
    await message.answer("Bosh menyu:", reply_markup=admin_main_kb())
