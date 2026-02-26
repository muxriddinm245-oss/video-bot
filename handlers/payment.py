from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

import database as db
from config import ADMIN_ID, CARD_NUMBER, CARD_OWNER
from keyboards.user_kb import cancel_payment_kb
from keyboards.admin_kb import payment_action_kb

router = Router()


class PaymentState(StatesGroup):
    waiting_screenshot = State()
    waiting_payment_for = State()


@router.callback_query(F.data.startswith("buy_"))
async def buy_course(callback: CallbackQuery, state: FSMContext):
    course_id = int(callback.data.split("_")[1])
    course = await db.get_course(course_id)

    if not course:
        await callback.answer("Kurs topilmadi!", show_alert=True)
        return

    already = await db.has_purchased(callback.from_user.id, course_id)
    if already:
        await callback.answer("✅ Siz bu kursni allaqachon sotib olgansiz!", show_alert=True)
        return

    price = course['price_uzs']
    await state.update_data(course_id=course_id)
    await state.set_state(PaymentState.waiting_screenshot)

    await callback.message.answer(
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"🎬 Kurs: <b>{course['title']}</b>\n"
        f"💰 To'lov miqdori: <b>{price:,} so'm</b>\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏦 <b>Karta raqami (nusxalash uchun bosing):</b>\n"
        f"<code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_OWNER}</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>Ko'rsatma:</b>\n"
        f"1️⃣ Yuqoridagi kartaga <b>{price:,} so'm</b> o'tkazing\n"
        f"2️⃣ To'lov chekining <b>screenshotini</b> (rasmini) shu yerga yuboring\n"
        f"3️⃣ Admin tekshirib, kursni ochib beradi ✅\n\n"
        f"⏱ Javob vaqti: <b>5-30 daqiqa</b>",
        reply_markup=cancel_payment_kb(),
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(PaymentState.waiting_screenshot, F.photo)
async def receive_screenshot(message: Message, state: FSMContext):
    data = await state.get_data()
    course_id = data.get('course_id')
    course = await db.get_course(course_id)

    if not course:
        await state.clear()
        await message.answer("❌ Xatolik yuz berdi. /start bosib qaytadan urining.")
        return

    screenshot_file_id = message.photo[-1].file_id
    payment_id = await db.add_pending_payment(message.from_user.id, course_id, screenshot_file_id)

    await state.clear()

    # Notify admin
    user = message.from_user
    try:
        await message.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=screenshot_file_id,
            caption=(
                f"💰 <b>Yangi to'lov so'rovi #{payment_id}</b>\n\n"
                f"👤 {user.full_name} (@{user.username or 'username yoq'})\n"
                f"🆔 ID: <code>{user.id}</code>\n"
                f"🎬 Kurs: <b>{course['title']}</b>\n"
                f"💵 Narx: <b>{course['price_uzs']:,} so'm</b>\n\n"
                f"✅ Tasdiqlash yoki ❌ rad etish:"
            ),
            reply_markup=payment_action_kb(payment_id, user.id),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await message.answer(
        "✅ <b>Screenshot qabul qilindi!</b>\n\n"
        "🔍 Admin to'lovingizni tekshirmoqda...\n"
        "⏱ 5-30 daqiqa ichida kurs ochiladi.\n\n"
        "Sabr qiling, xabar keladi! 🙏",
        parse_mode="HTML"
    )


@router.message(PaymentState.waiting_screenshot)
async def wrong_screenshot(message: Message):
    if message.text and "❌" in message.text:
        return
    await message.answer(
        "📸 Iltimos, faqat <b>to'lov chekining rasmi (screenshot)</b>ni yuboring!\n\n"
        "Chekda <b>summa</b> va <b>karta raqami</b> ko'rinishi kerak.",
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "❌ <b>To'lov bekor qilindi.</b>\n\n"
        "Kurs sotib olmoqchi bo'lsangiz, katalogdan qaytadan tanlang.",
        parse_mode="HTML"
    )


# ── Admin: approve / reject / message ──────────────────────────────────────

@router.callback_query(F.data.startswith("approve_"))
async def approve_payment(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    payment_id = int(callback.data.split("_")[1])
    payment = await db.get_pending_payment(payment_id)

    if not payment or payment['status'] != 'pending':
        await callback.answer("⚠️ Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await db.update_pending_status(payment_id, 'approved')
    await db.add_purchase(payment['user_id'], payment['course_id'])
    course = await db.get_course(payment['course_id'])

    try:
        await callback.bot.send_message(
            payment['user_id'],
            f"🎉 <b>Tabriklaymiz! To'lovingiz tasdiqlandi!</b>\n\n"
            f"🎬 <b>{course['title']}</b> kursi sizga ochildi!\n"
            f"📲 Video quyida yuborilmoqda...",
            parse_mode="HTML"
        )
        if course['video_file_id']:
            await callback.bot.send_video(
                payment['user_id'],
                video=course['video_file_id'],
                caption=(
                    f"🎬 <b>{course['title']}</b>\n\n"
                    f"✅ Kurs sizga tegishli — istalgan vaqt /start orqali ko'rishingiz mumkin!\n\n"
                    f"🚀 O'qishingizga muvaffaqiyat!"
                ),
                parse_mode="HTML"
            )
    except Exception as e:
        await callback.answer(f"Video yuborishda xato: {e}", show_alert=True)
        return

    await callback.message.edit_caption(
        callback.message.caption + "\n\n✅ <b>TASDIQLANDI — video yuborildi</b>",
        parse_mode="HTML",
        reply_markup=None
    )
    await callback.answer("✅ Tasdiqlandi, video yuborildi!")


@router.callback_query(F.data.startswith("reject_"))
async def reject_payment(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    payment_id = int(callback.data.split("_")[1])
    payment = await db.get_pending_payment(payment_id)

    if not payment or payment['status'] != 'pending':
        await callback.answer("⚠️ Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await db.update_pending_status(payment_id, 'rejected')

    try:
        await callback.bot.send_message(
            payment['user_id'],
            "❌ <b>To'lovingiz tasdiqlanmadi.</b>\n\n"
            "Mumkin bo'lgan sabab:\n"
            "• Screenshot noto'g'ri kartaga o'tkazilgan\n"
            "• Summa to'g'ri emas\n"
            "• Chek ko'rinmayapti\n\n"
            "To'g'ri to'lov qilib, screenshotni qayta yuboring 🙏\n"
            "Savollar uchun: /start → Admin bilan bog'lanish",
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.message.edit_caption(
        callback.message.caption + "\n\n❌ <b>RAD ETILDI</b>",
        parse_mode="HTML",
        reply_markup=None
    )
    await callback.answer("❌ Rad etildi!")


@router.callback_query(F.data.startswith("msg_user_"))
async def msg_user_start(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        return
    parts = callback.data.split("_")
    user_id = int(parts[2])
    payment_id = int(parts[3])
    await state.update_data(target_user_id=user_id, payment_id=payment_id)
    await state.set_state("admin_messaging")
    await callback.message.answer(
        "✏️ Foydalanuvchiga yuboriladigan xabarni yozing\n"
        "(yoki /cancel yozing bekor qilish uchun):"
    )
    await callback.answer()


@router.message(F.state == "admin_messaging")
async def admin_msg_send(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("Bekor qilindi.")
        return
    data = await state.get_data()
    try:
        await message.bot.send_message(data['target_user_id'], f"📩 <b>Admin xabari:</b>\n\n{message.text}", parse_mode="HTML")
        await message.answer("✅ Xabar yuborildi!")
    except Exception:
        await message.answer("❌ Xabar yuborishda xato!")
    await state.clear()
