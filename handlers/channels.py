import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, CallbackQueryHandler, filters

from config import ADMIN_ID

logger = logging.getLogger(__name__)

# Faqat config.py da majburiy kanallarni dastur tutadi (dynamic qilsangiz database bo'lsa yaxshi)
MANDATORY_CHANNELS = []

ADD_CHANNEL, REMOVE_CHANNEL = range(2)

def get_channels_list_text():
    if not MANDATORY_CHANNELS:
        return "📋 Majburiy kanallar ro'yxati hozircha BO'SH."
    text = "📋 Majburiy kanallar ro'yxati:\n"
    for i, ch in enumerate(MANDATORY_CHANNELS, 1):
        text += f"{i}. @{ch}\n"
    return text

async def add_channel_prompt(update: Update, context: CallbackContext):
    await update.callback_query.edit_message_text(
        "➕ Kanal username’ini (@ belgisiz) yuboring:"
    )
    return ADD_CHANNEL

async def add_channel(update: Update, context: CallbackContext):
    username = update.message.text.strip().replace("@", "")
    if not username.isalnum():
        await update.message.reply_text("❌ Xato! Kanal username’ini (@ belgisiz) yuboring.")
        return ADD_CHANNEL
    if username in MANDATORY_CHANNELS:
        await update.message.reply_text("❗️ Bu kanal ro'yxatda bor.")
        return ADD_CHANNEL
    MANDATORY_CHANNELS.append(username)
    await update.message.reply_text(
        f"✅ @{username} kanal qo'shildi!\n\n" + get_channels_list_text(),
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Ortga", callback_data="mandatory_channels")]
        ])
    )
    return ConversationHandler.END

async def remove_channel_prompt(update: Update, context: CallbackContext):
    if not MANDATORY_CHANNELS:
        await update.callback_query.edit_message_text(
            "❗️ Majburiy kanallar ro'yxati bo'sh!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Ortga", callback_data="mandatory_channels")]
            ])
        )
        return ConversationHandler.END
    buttons = [
        [InlineKeyboardButton(f"❌ {ch}", callback_data=f"del_ch_{ch}")]
        for ch in MANDATORY_CHANNELS
    ]
    buttons.append([InlineKeyboardButton("🔙 Ortga", callback_data="mandatory_channels")])
    await update.callback_query.edit_message_text(
        "❌ O'chirmoqchi bo'lgan kanalni tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return REMOVE_CHANNEL

async def remove_channel(update: Update, context: CallbackContext):
    query = update.callback_query
    chname = query.data.replace("del_ch_", "")
    if chname in MANDATORY_CHANNELS:
        MANDATORY_CHANNELS.remove(chname)
        text = f"❌ @{chname} kanal o'chirildi!\n\n" + get_channels_list_text()
    else:
        text = "❗️ Bunday kanal topilmadi.\n\n" + get_channels_list_text()
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Ortga", callback_data="mandatory_channels")]
        ])
    )
    return ConversationHandler.END

async def list_channels(update: Update, context: CallbackContext):
    text = get_channels_list_text()
    await update.callback_query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Ortga", callback_data="mandatory_channels")]
        ])
    )

# HANDLERLAR
add_channel_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(add_channel_prompt, pattern="add_channel")],
    states={
        ADD_CHANNEL: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_channel)],
    },
    fallbacks=[],
    per_message=False,
)

remove_channel_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(remove_channel_prompt, pattern="remove_channel")],
    states={
        REMOVE_CHANNEL: [CallbackQueryHandler(remove_channel, pattern="^del_ch_")],
    },
    fallbacks=[],
    per_message=False,
)

list_channels_handler = CallbackQueryHandler(list_channels, pattern="list_channel")

# Ushbu handlerlarni (add_channel_conv, remove_channel_conv, list_channels_handler)
# main.py yoki callback.py ichida app.add_handler() bilan ro'yxatdan o'tkazing

