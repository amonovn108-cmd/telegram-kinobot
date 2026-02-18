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

# ConversationHandler holatlari
VIDEO, NAME, CODE, CATEGORY, PARTS_COUNT, PART_VIDEOS, DESCRIPTION = range(7)


# ==================== ADMIN TEKSHIRISH ====================
async def is_admin(update: Update) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    user_id = update.effective_user.id
    return user_id == ADMIN_ID


# ==================== /ADDMOVIE - KINO QO'SHISH ====================
async def add_movie_start(update: Update, context: CallbackContext) -> int:
    """1-qadam: Kategoriya tanlash"""
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return ConversationHandler.END
    
    # Kategoriya tugmalari
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
        "🎬 YANGI KINO QO'SHISH\n\n"
        "1-qadam: KATEGORIYANI tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    return CATEGORY


async def add_movie_category(update: Update, context: CallbackContext) -> int:
    """Kategoriya tanlandi"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "addmov_cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END
    
    category = query.data.replace("addmov_cat_", "")
    context.user_data['new_movie_category'] = category
    category_emoji = CATEGORIES[category]['emoji']
    
    await query.edit_message_text(
        f"{category_emoji} {category.upper()} QO'SHISH\n\n"
        f"2-qadam: VIDEO yuboring:"
    )
    
    return VIDEO


async def add_movie_video(update: Update, context: CallbackContext) -> int:
    """2-qadam: Video qabul"""
    if update.message.video:
        file_id = update.message.video.file_id
        file_type = "video"
    elif update.message.document:
        file_id = update.message.document.file_id
        file_type = "document"
    else:
        await update.message.reply_text("❌ Iltimos, video yuboring!")
        return VIDEO
    
    context.user_data['new_movie_file_id'] = file_id
    context.user_data['new_movie_file_type'] = file_type
    
    category = context.user_data['new_movie_category']
    
    await update.message.reply_text(
        f"✅ Video qabul qilindi!\n\n"
        f"3-qadam: {category.upper()} NOMINI kiriting:"
    )
    
    return NAME


async def add_movie_name(update: Update, context: CallbackContext) -> int:
    """3-qadam: Nom"""
    name = update.message.text.strip()
    context.user_data['new_movie_name'] = name
    
    await update.message.reply_text(
        f"✅ Nom: {name}\n\n"
        f"4-qadam: KODINI kiriting (masalan: 1, 2, 3...):"
    )
    
    return CODE


async def add_movie_code(update: Update, context: CallbackContext) -> int:
    """4-qadam: Kod"""
    try:
        code = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Kod raqam bo'lishi kerak!")
        return CODE
    
    category = context.user_data['new_movie_category']
    
    # Shu kategoriyada kod mavjudligini tekshirish
    existing = db.get_movie_by_code(code)
    if existing and existing['category'] == category:
        await update.message.reply_text(
            f"❌ {category}da {code} kodli narsalar allaqachon mavjud!\n"
            f"Boshqa kod kiriting:"
        )
        return CODE
    
    context.user_data['new_movie_code'] = code
    
    # Agar serial bo'lsa - qismlar soni so'rash
    if category == "serial":
        await update.message.reply_text(
            f"✅ Kod: {code}\n\n"
            f"5-qadam: NEÇÇA QISMDAN IBORAT? (masalan: 5)"
        )
        return PARTS_COUNT
    else:
        # Kino yoki multfilm - tavsifga
        await update.message.reply_text(
            f"✅ Kod: {code}\n\n"
            f"5-qadam: TAVSIF kiriting:"
        )
        return DESCRIPTION


async def add_movie_parts_count(update: Update, context: CallbackContext) -> int:
    """5-qadam: Serial qismlari soni"""
    try:
        parts_count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Raqam kiriting!")
        return PARTS_COUNT
    
    context.user_data['new_movie_parts_count'] = parts_count
    context.user_data['new_movie_parts'] = []
    context.user_data['current_part'] = 1
    
    await update.message.reply_text(
        f"✅ {parts_count} qismli serial\n\n"
        f"6-qadam: 1-QISM VIDEOSINI yuboring:"
    )
    
    return PART_VIDEOS


async def add_movie_part_video(update: Update, context: CallbackContext) -> int:
    """6-qadam: Serial qismlari uchun video"""
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("❌ Video yuboring!")
        return PART_VIDEOS
    
    current_part = context.user_data.get('current_part', 1)
    parts_count = context.user_data.get('new_movie_parts_count', 1)
    
    # Qismni saqlash
    parts = context.user_data.get('new_movie_parts', [])
    parts.append({
        'name': f"{current_part}-qism",
        'file_id': file_id
    })
    context.user_data['new_movie_parts'] = parts
    
    # Keyingi qism
    if current_part < parts_count:
        context.user_data['current_part'] = current_part + 1
        await update.message.reply_text(
            f"✅ {current_part}-qism qabul qilindi!\n\n"
            f"{current_part + 1}-QISM VIDEOSINI yuboring:"
        )
        return PART_VIDEOS
    else:
        # Barcha qismlar yig'ildi
        await update.message.reply_text(
            f"✅ Barcha {parts_count} qism qabul qilindi!\n\n"
            f"7-qadam: TAVSIF kiriting:"
        )
        return DESCRIPTION


async def add_movie_description(update: Update, context: CallbackContext) -> int:
    """7-qadam: Tavsif va saqlash"""
    description = update.message.text.strip()
    
    # Ma'lumotlarni olish
    file_id = context.user_data.get('new_movie_file_id')
    file_type = context.user_data.get('new_movie_file_type')
    name = context.user_data['new_movie_name']
    code = context.user_data['new_movie_code']
    category = context.user_data['new_movie_category']
    parts = context.user_data.get('new_movie_parts', [])
    
    # Saqlash
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
            f"✅ MUVOFFAQIYATLI QO'SHILDI!\n\n"
            f"{category_emoji} {name}\n"
            f"🔢 Kod: {code}\n"
            f"🎞 {parts_text}\n"
            f"📝 {description}"
        )
        
        buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
        
        await update.message.reply_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await update.message.reply_text("❌ Xatolik yuz berdi!")
    
    context.user_data.clear()
    return ConversationHandler.END


# ==================== /DELETE - KINO O'CHIRISH ====================
async def delete_movie_start(update: Update, context: CallbackContext) -> int:
    """Delete - Kategoriya tanlash"""
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
        "🗑 KINO O'CHIRISH\n\n"
        "1-qadam: KATEGORIYANI tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
    return CATEGORY


async def delete_movie_category(update: Update, context: CallbackContext) -> int:
    """Kategoriya tanlandi"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "del_cancel":
        await query.edit_message_text("❌ Bekor qilindi.")
        return ConversationHandler.END
    
    category = query.data.replace("del_cat_", "")
    context.user_data['delete_category'] = category
    
    await query.edit_message_text(
        f"2-qadam: O'chirmoqchi bo'lgan KODINI kiriting:"
    )
    
    return CODE


async def delete_movie_code(update: Update, context: CallbackContext) -> int:
    """Kod kiritildi"""
    try:
        code = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Kod raqam bo'lishi kerak!")
        return CODE
    
    category = context.user_data.get('delete_category')
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await update.message.reply_text(
            f"❌ {code} kodli narsalar topilmadi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return CODE
    
    if movie['category'] != category:
        await update.message.reply_text(
            f"❌ Bu kod {movie['category']}da, siz {category}ni tanlagansiz!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return CODE
    
    # Tasdiqlovchi tugmalar
    parts_count = len(movie.get('parts', [1]))
    parts_text = f"{parts_count} qism" if parts_count > 1 else "1 qism"
    
    text = (
        f"TOPILDI:\n\n"
        f"{CATEGORIES[category]['emoji']} {movie['name']}\n"
        f"🔢 Kod: {code}\n"
        f"🎞 {parts_text}\n\n"
        f"⚠️ O'chirishni tasdiqlaysizmi?"
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
    """O'chirishni tasdiqlash"""
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
            f"{CATEGORIES[movie['category']]['emoji']} {movie['name']} (Kod: {code})",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
    else:
        await query.edit_message_text("❌ Xatolik!")


async def cancel_delete(update: Update, context: CallbackContext) -> None:
    """O'chirishni bekor qilish"""
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "❌ Bekor qilindi.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
        ]])
    )


# ==================== /SEND - XABAR YUBORISH ====================
async def send_message_start(update: Update, context: CallbackContext) -> None:
    """Xabar yuborish"""
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📢 XABAR YUBORISH\n\n"
            "Ishlatish: /send (xabar matni)"
        )
        return
    
    message = ' '.join(context.args)
    context.user_data['broadcast_message'] = message
    
    users_count = len(db.get_all_users())
    
    text = (
        f"📢 XABAR YUBORISH\n\n"
        f"Xabar: {message}\n"
        f"Qabul qiluvchilar: {users_count} ta\n\n"
        f"Yuborishni tasdiqlaysizmi?"
    )
    
    buttons = [
        [
            InlineKeyboardButton("✅ HA", callback_data="send_yes"),
            InlineKeyboardButton("❌ YO'Q", callback_data="send_no")
        ]
    ]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


async def broadcast_confirm(update: Update, context: CallbackContext) -> None:
    """Xabar yuborish tasdiqlash"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "send_no":
        await query.edit_message_text("❌ Bekor qilindi.")
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
            logger.error(f"Yuborish xatosi {user['user_id']}: {e}")
    
    result_text = (
        f"NATIJA\n\n"
        f"Yuborildi: {sent} ta\n"
        f"Yuborilmadi: {failed} ta"
    )
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await query.edit_message_text(result_text, reply_markup=InlineKeyboardMarkup(buttons))
    context.user_data.clear()


# ==================== /STATS - STATISTIKA ====================
async def stats_command(update: Update, context: CallbackContext) -> None:
    """Bot statistikasi"""
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return
    
    users = db.get_all_users()
    movies = db.get_all_movies()
    
    movies_by_cat = {'kino': 0, 'serial': 0, 'multfilm': 0}
    
    for movie in movies:
        cat = movie.get('category', 'kino')
        if cat in movies_by_cat:
            movies_by_cat[cat] += 1
    
    text = (
        f"BOT STATISTIKASI\n\n"
        f"FOYDALANUVCHILAR:\n"
        f"Jami: {len(users)} ta\n\n"
        f"KINOLAR:\n"
        f"Jami: {len(movies)} ta\n"
        f"Kino: {movies_by_cat['kino']} ta\n"
        f"Serial: {movies_by_cat['serial']} ta\n"
        f"Multfilm: {movies_by_cat['multfilm']} ta"
    )
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))


# ==================== CANCEL ====================
async def cancel(update: Update, context: CallbackContext) -> int:
    """Jarayonni bekor qilish"""
    await update.message.reply_text("❌ Bekor qilindi.")
    context.user_data.clear()
    return ConversationHandler.END


# ==================== HANDLERLAR ====================
add_movie_conv = ConversationHandler(
    entry_points=[CommandHandler("addmovie", add_movie_start)],
    states={
        CATEGORY: [CallbackQueryHandler(add_movie_category, pattern="^addmov_cat_|^addmov_cancel$")],
        VIDEO: [MessageHandler(filters.VIDEO | filters.Document.ALL, add_movie_video)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_name)],
        CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_code)],
        PARTS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_parts_count)],
        PART_VIDEOS: [MessageHandler(filters.VIDEO | filters.Document.ALL, add_movie_part_video)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=True
)

delete_movie_conv = ConversationHandler(
    entry_points=[CommandHandler("delete", delete_movie_start)],
    states={
        CATEGORY: [CallbackQueryHandler(delete_movie_category, pattern="^del_cat_|^del_cancel$")],
        CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_movie_code)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=True
)

confirm_delete_handler = CallbackQueryHandler(confirm_delete_movie, pattern="^confirm_del_")
cancel_delete_handler = CallbackQueryHandler(cancel_delete, pattern="^cancel_del$")

send_handler = CommandHandler("send", send_message_start)
broadcast_handler = CallbackQueryHandler(broadcast_confirm, pattern="^send_")

stats_handler = CommandHandler("stats", stats_command)
