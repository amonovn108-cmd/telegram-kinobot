import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext

from config import ADMIN_ID, CATEGORIES
from database import db

logger = logging.getLogger(__name__)

def get_main_menu(user_id):
    """Asosiy menyu tugmalarini yasaydi."""
    buttons = [
        [InlineKeyboardButton(f"{cat['emoji']} {cat['name']}", callback_data=f"cat_{cat_code}")]
        for cat_code, cat in CATEGORIES.items()
    ]
    # Faqat admin uchun "Admin panel" tugmasi qo‘shiladi
    if user_id == ADMIN_ID:
        buttons.append([InlineKeyboardButton("🛠 Admin panel", callback_data="admin_panel")])
    return InlineKeyboardMarkup(buttons)

async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = str(user.id)
    user_name = user.full_name
    username = user.username
    logger.info(f"📥 /start: {user_name} ({user_id})")

    # Foydalanuvchini databasega qo'shish (yangilik tekshiruvi)
    is_new = db.add_user(user_id, username, user_name)

    if is_new and user_id != str(ADMIN_ID):
        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"🆕 <b>YANGI FOYDALANUVCHI</b>\n\n"
                    f"👤 Ism: {user_name}\n"
                    f"🆔 ID: <code>{user_id}</code>\n"
                    f"📱 Username: @{username if username else 'yoq'}"
                ),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xatolik: {e}")

    menu = get_main_menu(int(user_id))
    await update.message.reply_text(
        f"👋 Assalomu alaykum, <b>{user_name}</b>!\n\nKategoriyani tanlang yoki admin paneldan foydalaning.",
        reply_markup=menu,
        parse_mode="HTML"
    )

# Handler hosil qilamiz
start_handler = CommandHandler("start", start)
