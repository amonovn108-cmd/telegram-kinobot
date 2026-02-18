import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackContext,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler
)
from database import db
from config import ADMIN_ID, CATEGORIES

logger = logging.getLogger(__name__)

VIDEO, NAME, CODE, CATEGORY, PARTS_COUNT, PART_VIDEOS, DESCRIPTION = range(7)


async def is_admin(update: Update) -> bool:
    user_id = update.effective_user.id
    return user_id == ADMIN_ID


# ==================== /ADDMOVIE ====================
async def add_movie_start(update: Update, context: CallbackContext) -> int:
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return ConversationHandler.END
    
    buttons = []
    row = []
    
    for i, (code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"addmov_cat_{code}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("❌ BEKOR", callback_data="addmov_cancel")])
    
    await update.message.reply_text(
        "🎬 YANGI QO'SHISH\n\n"
        "1️⃣ KATEGORIYANI tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    return CATEGORY


async def add_movie_category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "addmov_cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END
    
    category = query.data.replace("addmov_cat_", "")
    context.user_data['new_movie_category'] = category
    category_emoji = CATEGORIES[category]['emoji']
    
    await query.edit_message_text(
        f"{category_emoji} {category.upper()}\n\n"
        f"2️⃣ VIDEO yuboring:"
    )
    
    return VIDEO


async def add_movie_video(update: Update, context: CallbackContext) -> int:
    if update.message.video:
        file_id = update.message.video.file_id
        file_type = "video"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
    else:
        await update.message.reply_text("❌ Video yuboring!")
        return VIDEO
    
    context.user_data['new_movie_file_id'] = file_id
    context.user_data['new_movie_file_type'] = file_type
    
    await update.message.reply_text(
        "✅ Video qabul!\n\n"
        "3️⃣ NOMINI kiriting:"
    )
    
    return NAME


async def add_movie_name(update: Update, context: CallbackContext) -> int:
    name = update.message.text.strip()
    context.user_data['new_movie_name'] = name
    
    await update.message.reply_text(
        f"✅ Nom: {name}\n\n"
        f"4️⃣ KODINI kiriting (1, 2, 3...):"
    )
    
    return CODE


async def add_movie_code(update: Update, context: CallbackContext) -> int:
    try:
        code = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Raqam kiriting!")
        return CODE
    
    category = context.user_data['new_movie_category']
    existing = db.get_movie_by_code(code)
    
    if existing and existing['category'] == category:
        await update.message.reply_text(
            f"❌ Bu kategoriyada {code} allaqachon bor!\n"
            f"Boshqa kod:"
        )
        return CODE
    
    context.user_data['new_movie_code'] = code
    
    if category == "serial":
        await update.message.reply_text(
            f"✅ Kod: {code}\n\n"
            f"5️⃣ NEÇÇA QISMDAN IBORAT?"
        )
        return PARTS_COUNT
    else:
        await update.message.reply_text(
            f"✅ Kod: {code}\n\n"
            f"5️⃣ TAVSIF kiriting:"
        )
        return DESCRIPTION


async def add_movie_parts_count(update: Update, context: CallbackContext) -> int:
    try:
        parts_count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Raqam!")
        return PARTS_COUNT
    
    context.user_data['new_movie_parts_count'] = parts_count
    context.user_data['new_movie_parts'] = []
    context.user_data['current_part'] = 1
    
    await update.message.reply_text(
        f"✅ {parts_count} qismli\n\n"
        f"6️⃣ 1-QISM VIDEOSINI yuboring:"
    )
    
    return PART_VIDEOS


async def add_movie_part_video(update: Update, context: CallbackContext) -> int:
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("❌ Video!")
        return PART_VIDEOS
    
    current_part = context.user_data.get('current_part', 1)
    parts_count = context.user_data.get('new_movie_parts_count', 1)
    
    parts = context.user_data.get('new_movie_parts', [])
    parts.append({
        'name': f"{current_part}-qism",
        'file_id': file_id
    })
    context.user_data['new_movie_parts'] = parts
    
    if current_part < parts_count:
        context.user_data['current_part'] = current_part + 1
        await update.message.reply_text(
            f"✅ {current_part}-qism!\n\n"
            f"{current_part + 1}-QISM VIDEOSINI yuboring:"
        )
        return PART_VIDEOS
    else:
        await update.message.reply_text(
            f"✅ Barcha {parts_count} qism!\n\n"
            f"7️⃣ TAVSIF kiriting:"
        )
        return DESCRIPTION


async def add_movie_description(update: Update, context: CallbackContext) -> int:
    description = update.message.text.strip()
    
    file_id = context.user_data.get('new_movie_file_id')
    file_type = context.user_data.get('new_movie_file_type')
    name = context.user_data['new_movie_name']
    code = context.user_data['new_movie_code']
    category = context.user_data['new_movie_category']
    parts = context.user_data.get('new_movie_parts', [])
    
    if category == "serial" and parts:
        success = db.add_serial(
            code=code,
            name=name,
            category=category,
            description=description,
            parts=parts
        )
        parts_text = f"{len(parts)} qism"
    else:
        success = db.add_movie(
            code=code,
            name=name,
            category=category,
            description=description,
            file_id=file_id,
            file_type=file_type
        )
        parts_text = "1 qism"
    
    if success:
        category_emoji = CATEGORIES[category]['emoji']
        
        result_text = (
            f"✅ SAQLANDI!\n\n"
            f"{category_emoji} {name}\n"
            f"🔢 {code}\n"
            f"🎞 {parts_text}"
        )
        
        buttons = [[InlineKeyboardButton("🏠 MENYU", callback_data="back_to_main")]]
        await update.message.reply_text(result_text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.message.reply_text("❌ Xatolik!")
    
    context.user_data.clear()
    return ConversationHandler.END


# ==================== /DELETE ====================
async def delete_movie_start(update: Update, context: CallbackContext) -> int:
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return ConversationHandler.END
    
    buttons = []
    row = []
    
    for i, (code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"del_cat_{code}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("❌ BEKOR", callback_data="del_cancel")])
    
    await update.message.reply_text(
        "🗑 O'CHIRISH\n\n"
        "1️⃣ KATEGORIYANI tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    return CATEGORY


async def delete_movie_category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    
    if query.data == "del_cancel":
        await query.edit_message_text("❌ Bekor.")
        return ConversationHandler.END
    
    category = query.data.replace("del_cat_", "")
    context.user_data['delete_category'] = category
    
    await query.edit_message_text(f"2️⃣ KODINI kiriting:")
    
    return CODE


async def delete_movie_code(update: Update, context: CallbackContext) -> int:
    try:
        code = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Raqam!")
        return CODE
    
    category = context.user_data.get('delete_category')
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await update.message.reply_text(
            f"❌ {code} topilmadi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 MENYU", callback_data="back_to_main")
            ]])
        )
        return CODE
    
    if movie['category'] != category:
        await update.message.reply_text(
            f"❌ Bu {movie['category']}da!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 MENYU", callback_data="back_to_main")
            ]])
        )
        return CODE
    
    parts_count = len(movie.get('parts', [1]))
    parts_text = f"{parts_count} qism" if parts_count > 1 else "1 qism"
    
    text = (
        f"TOPILDI:\n\n"
        f"{CATEGORIES[category]['emoji']} {movie['name']}\n"
        f"🔢 {code}\n"
        f"🎞 {parts_text}\n\n"
        f"O'chirishni tasdiqlaysizmi?"
    )
    
    buttons = [
        [
            InlineKeyboardButton("✅ HA", callback_data=f"confirm_del_{code}"),
            InlineKeyboardButton("❌ YO'Q", callback_data="cancel_del")
        ]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))
    
    return ConversationHandler.END


async def confirm_delete_movie(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    code = int(query.data.replace("confirm_del_", ""))
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await query.edit_message_text("❌ Topilmadi!")
        return
    
    success = db.delete_movie(code)
    
    if success:
        await query.edit_message_text(
            f"✅ O'CHIRILDI!\n\n"
            f"{CATEGORIES[movie['category']]['emoji']} {movie['name']}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 MENYU", callback_data="back_to_main")
            ]])
        )
    else:
        await query.edit_message_text("❌ Xatolik!")


async def cancel_delete(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ Bekor.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 MENYU", callback_data="back_to_main")
        ]])
    )


# ==================== /SEND ====================
async def send_message_start(update: Update, context: CallbackContext) -> None:
    if not await is_admin(update):
        await update.message.reply_text("❌ Faqat admin!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "XABAR: /send (matn)\n\n"
            "Misol: /send Yangi kino qo'shildi!"
        )
        return
    
    message = ' '.join(context.args)
    context.user_data['broadcast_message'] = message
    
    users_count = len(db.get_all_users())
    
    text = (
        f"XABAR YUBORISH\n\n"
        f"Xabar: {message}\n"
        f"Qabul: {users_count} ta\n\n"
        f"Tasdiqlaysizmi?"
    )
    
    buttons = [
        [
            InlineKeyboardButton("✅ HA", callback_data="send_yes"),
            InlineKeyboardButton("❌ YO'Q", callback_data="send_no")
        ]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def broadcast_confirm(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    
    if query.data == "send_no":
        await query.edit_message_text("❌ Bekor.")
        context.user_data.clear()
        return
    
    message = context.user_data.get('broadcast_message', '')
    users = db.get_all_users()
    
    await query.edit_message_text(f"Yuborilmoqda... ({len(users)} ta)")
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=int(user['user_id']),
                text=message
            )
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"Yuborish xatosi: {e}")
    
    result_text = (
        f"NATIJA\n\n"
        f"Yuborildi: {sent} ta\n"
        f"Yuborilmadi: {failed} ta"
    )
    
    buttons = [[InlineKeyboardButton("🏠 MENYU", callback_data="back_to_main")]]
    await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data.clear()


# ==================== /STATS ====================
async def stats_command(update: Update, context: CallbackContext) -> None:
    if not await is_admin(update):
        await update.message.reply_text("❌ Faqat admin!")
        return
    
    users = db.get_all_users()
    movies = db.get_all_movies()
    
    movies_by_cat = {'kino': 0, 'serial': 0, 'multfilm': 0}
    
    for movie in movies:
        cat = movie.get('category', 'kino')
        if cat in movies_by_cat:
            movies_by_cat[cat] += 1
    
    text = (
        f"STATISTIKA\n\n"
        f"FOYDALANUVCHILAR: {len(users)} ta\n\n"
        f"KINOLAR: {len(movies)} ta\n"
        f"Kino: {movies_by_cat['kino']} ta\n"
        f"Serial: {movies_by_cat['serial']} ta\n"
        f"Multfilm: {movies_by_cat['multfilm']} ta"
    )
    
    buttons = [[InlineKeyboardButton("🏠 MENYU", callback_data="back_to_main")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ==================== CANCEL ====================
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("❌ Bekor.")
    context.user_data.clear()
    return ConversationHandler.END


# ==================== HANDLERS ====================
add_movie_conv = ConversationHandler(
    entry_points=[CommandHandler("addmovie", add_movie_start)],
    states={
        CATEGORY: [CallbackQueryHandler(add_movie_category, pattern="^addmov_")],
        VIDEO: [MessageHandler(filters.VIDEO | filters.Document.ALL, add_movie_video)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_name)],
        CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_code)],
        PARTS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_parts_count)],
        PART_VIDEOS: [MessageHandler(filters.VIDEO | filters.Document.ALL, add_movie_part_video)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False
)

delete_movie_conv = ConversationHandler(
    entry_points=[CommandHandler("delete", delete_movie_start)],
    states={
        CATEGORY: [CallbackQueryHandler(delete_movie_category, pattern="^del_")],
        CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_movie_code)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False
)

confirm_delete_handler = CallbackQueryHandler(confirm_delete_movie, pattern="^confirm_del_")
cancel_delete_handler = CallbackQueryHandler(cancel_delete, pattern="^cancel_del$")

send_handler = CommandHandler("send", send_message_start)
broadcast_handler = CallbackQueryHandler(broadcast_confirm, pattern="^send_")

stats_handler = CommandHandler("stats", stats_command)
