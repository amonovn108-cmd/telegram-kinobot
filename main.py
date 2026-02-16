import os
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

# Config
from config import BOT_TOKEN, ADMIN_ID

# Handlers
from handlers.start import start_handler
from handlers.callback import callback_handler
from handlers.movie import search_handler  # Endi bu ishlaydi!
from handlers.admin import (
    add_movie_conv,
    delete_command,
    delete_category_handler,
    delete_code_handler,
    back_to_delete_handler,
    send_command,
    broadcast_handler,
    stats_command_handler,
    cancel_command
)
from handlers.error import error_handler

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Botni ishga tushirish"""
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi!")
        return
    
    logger.info(f"✅ Admin ID: {ADMIN_ID} (type: {type(ADMIN_ID)})")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlerlarni qo'shish
    app.add_handler(start_handler)                              # /start
    app.add_handler(CallbackQueryHandler(callback_handler))     # Tugmalar
    app.add_handler(search_handler)                             # Matn qidirish (Endi xatosiz!)
    
    # Admin handlerlar
    app.add_handler(add_movie_conv)
    app.add_handler(delete_command)
    app.add_handler(delete_category_handler)
    app.add_handler(delete_code_handler)
    app.add_handler(back_to_delete_handler)
    app.add_handler(send_command)
    app.add_handler(broadcast_handler)
    app.add_handler(stats_command_handler)
    app.add_handler(cancel_command)
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logger.info("✅ Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
