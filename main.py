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
from config import BOT_TOKEN

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
        logger.error("BOT_TOKEN topilmadi!")
        return
    
    # Application yaratish
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # ============ HANDLERLARNI QO'SHISH ============
    
    # 1. START HANDLER - asosiy
    app.add_handler(start_handler)
    
    # 2. CALLBACK HANDLER - barcha tugmalar
    app.add_handler(CallbackQueryHandler(callback_handler))
    
    # 3. MOVIE HANDLER - kino qidirish
    app.add_handler(search_handler)
    
    # 4. ADMIN HANDLERS - kino qo'shish (conversation)
    app.add_handler(add_movie_conv)
    
    # 5. ADMIN DELETE HANDLERS
    app.add_handler(delete_command)
    app.add_handler(delete_category_handler)
    app.add_handler(delete_code_handler)
    app.add_handler(back_to_delete_handler)
    
    # 6. ADMIN SEND HANDLERS
    app.add_handler(send_command)
    app.add_handler(broadcast_handler)
    
    # 7. ADMIN STATS HANDLER
    app.add_handler(stats_command_handler)
    
    # 8. ADMIN CANCEL HANDLER
    app.add_handler(cancel_command)
    
    # 9. ERROR HANDLER (eng oxirgi)
    app.add_error_handler(error_handler)
    
    # Botni ishga tushirish
    logger.info("✅ Bot ishga tushdi...")
    logger.info(f"👤 Admin ID: {ADMIN_ID}")
    
    app.run_polling()


if __name__ == "__main__":
    main()
