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
from config import BOT_TOKEN, ADMIN_ID  # ADMIN_ID int bo'lishi kerak

# Handlers
from handlers.start import start_handler
from handlers.callback import callback_handler
from handlers.movie import search_handler
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
    
    # Bot tokenini tekshirish
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN topilmadi!")
        return
    
    logger.info(f"✅ Admin ID: {ADMIN_ID} (type: {type(ADMIN_ID)})")  # int ekanligini tekshirish
    
    # Application yaratish
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Handlerlarni qo'shish
    app.add_handler(start_handler)                              # /start
    app.add_handler(CallbackQueryHandler(callback_handler))     # Tugmalar
    app.add_handler(search_handler)                              # Matn qidirish
    
    # Admin handlerlar
    app.add_handler(add_movie_conv)                              # /addmovie
    app.add_handler(delete_command)                              # /delete
    app.add_handler(delete_category_handler)                     # delete category
    app.add_handler(delete_code_handler)                         # delete code
    app.add_handler(back_to_delete_handler)                      # back to delete
    app.add_handler(send_command)                                 # /send
    app.add_handler(broadcast_handler)                            # broadcast confirm
    app.add_handler(stats_command_handler)                        # /stats
    app.add_handler(cancel_command)                               # /cancel
    
    # Error handler
    app.add_error_handler(error_handler)
    
    logger.info("✅ Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
