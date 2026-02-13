import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, CallbackContext
from datetime import datetime
from config import ADMIN_ID, MANDATORY_CHANNELS, CATEGORIES
from database import db

logger = logging.getLogger(__name__)


async def check_subscription(update: Update, context: CallbackContext):
    """Obunani tekshirish"""
    user_id = update.effective_user.id
    not_subscribed = []
    channel_info = []
    
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
                try:
                    chat = await context.bot.get_chat(f"@{channel}")
                    channel_info.append({
                        "username": channel,
                        "title": chat.title or channel
                    })
                except:
                    channel_info.append({
                        "username": channel,
                        "title": channel
                    })
        except Exception as e:
            logger.warning(f"⚠️ Kanal tekshirishda xatolik @{channel}: {e}")
            not_subscribed.append(channel)
            channel_info.append({
                "username": channel,
                "title": channel
            })
    
    return len(not_subscribed) == 0, not_subscribed, channel_info


async def start(update: Update, context: CallbackContext):
    """START komandasi"""
    user_id = str(update.effective_user.id)  # ✅ String!
    user_name = update.effective_user.full_name
    username = update.effective_user.username
    
    logger.info(f"📥 /start: {user_name} ({user_id})")
    
    # Obunani tekshirish
    is_subscribed, _, channels_info = await check_subscription(update, context)
    
    if not is_subscribed:
        await show_subscription_message(update, channels_info)
        return
    
    # Foydalanuvchini databasega qo'shish
    is_new = db.add_user(user_id, username, user_name)
    
    # Yangi foydalanuvchi bo'lsa, adminga xabar
    if is_new and user_id != ADMIN_ID:  # ✅ String bilan solishtirish
        try:
            admin_text = (
                f"🆕 <b>YANGI FOYDALANUVCHI</b>\n\n"
                f"👤 Ism: {user_name}\n"
                f"🆔 ID: <code>{user_id}</code>\n"
                f"📱 Username: @{username if username else 'yoq'}\n"
                f"📅 Sana: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,  # ✅ String!
                text=admin_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Adminga xabar yuborishda xatolik: {e}")
    
    # Asosiy menyu
    await show_main_menu(update, context, user_name)


async def show_main_menu(update: Update, context: CallbackContext, user_name: str):
    """Asosiy menyu"""
    buttons = []
    
    for code, cat in CATEGORIES.items():
        buttons.append([InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"cat_{code}"
        )])
    
    buttons.append([InlineKeyboardButton(
        "📋 KINOLAR RO'YXATI", 
        callback_data="show_movielist"
    )])
    
    await update.message.reply_text(
        f"👋 Assalomu alaykum, <b>{user_name}</b>!\n\n"
        f"Kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def show_subscription_message(update: Update, channels_info: list):
    """Obuna xabari"""
    text = "🔒 <b>BOTDAN FOYDALANISH UCHUN OBUNA BO'LING</b>\n\n"
    text += "📢 <b>MAJBURIY KANALLAR:</b>\n"
    
    for ch in channels_info:
        text += f"└─ 📌 <a href='https://t.me/{ch['username']}'>{ch['title']}</a>\n"
    
    text += "\n✅ <b>Barcha kanallarga obuna bo'lib, tugmani bosing!</b>"
    
    buttons = []
    for ch in channels_info:
        buttons.append([InlineKeyboardButton(
            f"📢 {ch['title']}",
            url=f"https://t.me/{ch['username']}"
        )])
    
    buttons.append([InlineKeyboardButton(
        "✅ OBUNA BO'LDIM",
        callback_data="check_subscription"
    )])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def back_to_main(update: Update, context: CallbackContext):
    """Asosiy menyuga qaytish"""
    query = update.callback_query
    await query.answer()
    
    user_name = update.effective_user.full_name
    
    buttons = []
    for code, cat in CATEGORIES.items():
        buttons.append([InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"cat_{code}"
        )])
    
    buttons.append([InlineKeyboardButton(
        "📋 KINOLAR RO'YXATI", 
        callback_data="show_movielist"
    )])
    
    await query.edit_message_text(
        f"👋 <b>{user_name}</b>, asosiy menyu:\n\n"
        f"Kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def show_help(update: Update, context: CallbackContext):
    """Yordam"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "🆘 <b>YORDAM</b>\n\n"
        "📌 Kategoriya tanlang\n"
        "📌 Kino kodini kiriting\n"
        "📌 Kinoni tomosha qiling\n\n"
        "📋 /movielist - barcha kinolar"
    )
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await query.edit_message_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


# Handlerlar
start_handler = CommandHandler("start", start)
back_handler = CallbackQueryHandler(back_to_main, pattern="^back_to_main$")
help_handler = CallbackQueryHandler(show_help, pattern="^show_help$")
