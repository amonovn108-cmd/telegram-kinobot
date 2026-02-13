import os
import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)
from config import ADMIN_ID, MANDATORY_CHANNELS, CATEGORIES
from database import db

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ================= SUBSCRIPTION CHECK =================
async def check_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    not_subscribed = []

    for channel in MANDATORY_CHANNELS:
        channel = channel.strip()
        if not channel:
            continue

        try:
            member = await context.bot.get_chat_member(
                chat_id=f"@{channel}",
                user_id=user_id
            )

            if member.status in ["left", "kicked"]:
                not_subscribed.append(channel)

        except Exception as e:
            logger.warning(f"Kanal tekshirishda xatolik @{channel}: {e}")
            not_subscribed.append(channel)

    return len(not_subscribed) == 0, not_subscribed


# ================= START COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.full_name
    username = user.username

    is_subscribed, channels = await check_subscription(update, context)

    if not is_subscribed:
        buttons = []

        for channel in channels:
            buttons.append([
                InlineKeyboardButton(
                    f"📢 @{channel}",
                    url=f"https://t.me/{channel}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "✅ Obuna bo'ldim!",
                callback_data="obuna_tekshir"
            )
        ])

        text = "⚠️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:\n\n"
        for ch in channels:
            text += f"📢 @{ch}\n"

        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return

    # Database
    db.add_user(user_id, username, user_name)

    # Menu
    buttons = [
        [InlineKeyboardButton(
            cat["emoji"] + " " + cat["name"],
            callback_data=f"kategoriya_{code}"
        )]
        for code, cat in CATEGORIES.items()
    ]

    await update.message.reply_text(
        f"👋 Assalomu alaykum {user_name}!\n\nKategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    logger.info(f"Yangi foydalanuvchi: {user_name} ({user_id})")


# ================= CALLBACK =================
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "obuna_tekshir":
        is_subscribed, channels = await check_subscription(update, context)

        if is_subscribed:
            await query.edit_message_text("✅ Obuna tasdiqlandi! /start ni qayta bosing.")
        else:
            await query.answer("❌ Hali ham obuna bo‘lmagansiz!", show_alert=True)


# ================= MAIN =================
def main():
    token = os.getenv("BOT_TOKEN")

    if not token:
        raise ValueError("BOT_TOKEN topilmadi!")

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    logger.info("Bot ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    main()

