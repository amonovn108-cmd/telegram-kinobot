import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext
from config import ADMIN_ID, MANDATORY_CHANNELS, CATEGORIES
from database import db

logger = logging.getLogger(__name__)


async def check_subscription(update: Update, context: CallbackContext) -> bool:
    """Obunani tekshirish"""
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
            logger.warning(f"⚠️ Kanal tekshirishda xatolik @{channel}: {e}")
            not_subscribed.append(channel)
    
    return len(not_subscribed) == 0, not_subscribed


async def start(update: Update, context: CallbackContext) -> None:
    """START komandasi"""
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    username = update.effective_user.username
    
    # Obunani tekshirish
    is_subscribed, channels = await check_subscription(update, context)
    
    if not is_subscribed:
        buttons = []
        for channel in channels:
            buttons.append([InlineKeyboardButton(
                f"📢 @{channel}",
                url=f"https://t.me/{channel}"
            )])
        buttons.append([InlineKeyboardButton(
            "✅ Obuna bo'ldim!",
            callback_data="obuna_tekshir"
        )])
        
        message = "⚠️ <b>Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
        for channel in channels:
            message += f"📢 @{channel}\n"
        message += "\nObuna bo'lganingizdan keyin <b>✅ Obuna bo'ldim!</b> tugmasini bosing."
        
        await update.message.reply_text(
            message,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )
        return
    
    # Foydalanuvchini database-ga qo'shish
    db.add_user(user_id, username, user_name)
    
    # Menyu tugmalari
    buttons = [
        [InlineKeyboardButton(cat["emoji"] + " " + cat["name"], 
                            callback_data=f"kategoriya_{code}")]
        for code, cat in CATEGORIES.items()
    ]
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, <b>{user_name}</b>!\n"
        f"🎥 Kino Botiga xush kelibsiz!\n\n"
        f"Quyidagi kategoriyalardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )
    
    logger.info(f"✅ Yangi foydalanuvchi: {user_name} ({user_id})")


# Handler registration
start_handler = CommandHandler("start", start)
