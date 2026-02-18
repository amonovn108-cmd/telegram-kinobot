import os
import logging
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, ADMIN_ID

from handlers.start import start_handler
from handlers.callback import callback_handler
from handlers.movie import search_handler
from handlers.admin import (
    add_movie_conv,
    delete_movie_conv,
    confirm_delete_handler,
    cancel_delete_handler,
    send_handler,
    broadcast_handler,
    stats_handler
)
from handlers.error import error_handler

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Botni ishga tushirish"""
    
    if not BOT_TOKEN:
        logger.error("❌ BOT_TOKEN yo'q!")
        return
    
    logger.info(f"✅ Admin ID: {ADMIN_ID}")
    
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # ==================== ODDIY HANDLERLAR ====================
    app.add_handler(start_handler)                              # /start
    app.add_handler(CallbackQueryHandler(callback_handler))     # Tugmalar
    app.add_handler(search_handler)                             # Kino qidirish
    
    # ==================== ADMIN HANDLERLAR ====================
    # Add movie
    app.add_handler(add_movie_conv)
    
    # Delete movie
    app.add_handler(delete_movie_conv)
    app.add_handler(confirm_delete_handler)
    app.add_handler(cancel_delete_handler)
    
    # Send broadcast
    app.add_handler(send_handler)
    app.add_handler(broadcast_handler)
    
    # Stats
    app.add_handler(stats_handler)
    
    # ==================== ERROR HANDLER ====================
    app.add_error_handler(error_handler)
    
    logger.info("✅ Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()
