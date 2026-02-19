import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

from config import ADMIN_ID, CATEGORIES

logger = logging.getLogger(__name__)

async def callback_handler(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(update.effective_user.id)

    logger.info(f"🔹 Callback: {data}")

    # ========== ADMIN PANEL OCHISH ==========
    if data == "admin_panel" and user_id == str(ADMIN_ID):
        admin_buttons = [
            [InlineKeyboardButton("➕ Kino qo‘shish", callback_data="add_movie")],
            [InlineKeyboardButton("🗑 Kino o‘chirish", callback_data="delete_movie")],
            [InlineKeyboardButton("📊 Statistika", callback_data="stats")],
            [InlineKeyboardButton("📢 Xabar yuborish", callback_data="send_broadcast")],
            [InlineKeyboardButton("🔗 Majburiy kanallar", callback_data="mandatory_channels")],  # <-- YANGI TUGMA
            [InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_to_main")]
        ]
        await query.edit_message_text(
            "🛠 <b>Admin paneli</b>\nKerakli bo‘limni tanlang:",
            reply_markup=InlineKeyboardMarkup(admin_buttons),
            parse_mode="HTML"
        )

    # ========== MAJBURIY KANALLAR SUBMENUSI ==========
    elif data == "mandatory_channels" and user_id == str(ADMIN_ID):
        channels_buttons = [
            [InlineKeyboardButton("➕ Kanal qo‘shish", callback_data="add_channel")],
            [InlineKeyboardButton("❌ Kanal o‘chirish", callback_data="remove_channel")],
            [InlineKeyboardButton("📋 Kanallar ro‘yxati", callback_data="list_channel")],
            [InlineKeyboardButton("🔙 Ortga", callback_data="admin_panel")]
        ]
        await query.edit_message_text(
            "🔗 <b>Majburiy kanallar sozlamalari</b>\nPastdan kerakli amalni tanlang:",
            reply_markup=InlineKeyboardMarkup(channels_buttons),
            parse_mode="HTML"
        )

    # ... Boshqa callbacklar shu joyda davom etadi (kategoriya, kino, stat, ...)
    # (Misol uchun, oldingi javoblarimdagi kabi boshqa bloklar bo'lishi kerak)

    else:
        await query.answer("❌ Bu tugma hozircha ishlamaydi.", show_alert=True)
        logger.warning(f"Nomaʼlum yoki ruxsat etilmagan callback: {data}")
