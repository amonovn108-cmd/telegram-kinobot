import logging
from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID

logger = logging.getLogger(__name__)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Asinxron xatolik handleri. Har qanday kutilmagan xatolikda admin va foydalanuvchini ogohlantiradi."""
    # Logga yozish
    logger.error(msg="❌ Exception in handler", exc_info=context.error)

    # Xatolik tafsilotlari
    try:
        tb = str(context.error)
        user_id = None
        if update and hasattr(update, "effective_user") and update.effective_user:
            user_id = update.effective_user.id

        # Adminga xabar
        if ADMIN_ID and user_id != ADMIN_ID:
            try:
                context.bot and await context.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=f"❗️ Botda xatolik:\n\n{tb}"
                )
            except Exception as e:
                logger.warning(f"Admin xabariga xato: {e}")

        # Userga xabar
        if update and hasattr(update, "message") and update.message:
            try:
                await update.message.reply_text(
                    "❌ Texnik xatolik. Birozdan so‘ng qayta urinib ko‘ring.",
                )
            except Exception:
                pass
        elif update and hasattr(update, "callback_query") and update.callback_query:
            try:
                await update.callback_query.answer(
                    "❌ Texnik xatolik. Keyinroq urinib ko‘ring.", show_alert=True
                )
            except Exception:
                pass
    except Exception as e:
        logger.error(f"Xatolikni boshqarishda xato: {e}")
