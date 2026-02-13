import logging
import traceback
from telegram import Update
from telegram.ext import CallbackContext
from config import ADMIN_ID

logger = logging.getLogger(__name__)


async def error_handler(update: Update, context: CallbackContext) -> None:
    """Barcha xatoliklarni ushlash va qayta ishlash"""
    
    # Xatolik ma'lumotlarini yig'ish
    error = context.error
    error_traceback = "".join(traceback.format_tb(error.__traceback__))
    error_type = type(error).__name__
    error_message = str(error)
    
    # Logga yozish
    logger.error(f"❌ Xatolik yuz berdi: {error_type}: {error_message}")
    logger.error(f"Traceback:\n{error_traceback}")
    
    # Foydalanuvchi ma'lumotlari
    user = update.effective_user if update else None
    chat = update.effective_chat if update else None
    message = update.effective_message if update else None
    
    user_info = f"Noma'lum foydalanuvchi"
    if user:
        user_info = f"👤 {user.full_name} (ID: {user.id})"
    
    chat_info = f"Noma'lum chat"
    if chat:
        chat_info = f"💬 {chat.title if chat.title else 'Shaxsiy'} (ID: {chat.id})"
    
    message_info = f"Hech qanday xabar"
    if message:
        message_text = message.text if message.text else "Media xabar"
        message_info = f"📝 {message_text[:100]}"
    
    # Foydalanuvchiga xabar
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "⚠️ <b>Texnik xatolik yuz berdi!</b>\n"
                "Admin xabardor qilindi. Tez orada muammo hal qilinadi.",
                parse_mode="HTML"
            )
        except:
            pass
    
    # Adminga xabar yuborish
    admin_text = (
        f"🚨 <b>XATOLIK YUZ BERDI!</b>\n\n"
        f"<b>Foydalanuvchi:</b> {user_info}\n"
        f"<b>Chat:</b> {chat_info}\n"
        f"<b>Xabar:</b> {message_info}\n\n"
        f"<b>Xatolik turi:</b> {error_type}\n"
        f"<b>Xatolik:</b> {error_message[:200]}\n\n"
        f"<b>Traceback:</b>\n<code>{error_traceback[:500]}</code>"
    )
    
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Adminga xatolik xabarini yuborishda xatolik: {e}")
