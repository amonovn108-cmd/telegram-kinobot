import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler, CommandHandler, MessageHandler, filters
from database import db
from config import ADMIN_ID, CATEGORIES

logger = logging.getLogger(__name__)

# ConversationHandler holatlari
VIDEO, NAME, CODE, CATEGORY, PARTS_COUNT, DESCRIPTION = range(6)


# ==================== ADMIN TEKSHIRISH ====================
async def is_admin(update: Update) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish"""
    user_id = update.effective_user.id
    return user_id == ADMIN_ID


# ==================== /ADDMOVIE - KINO QO'SHISH ====================
async def add_movie_start(update: Update, context: CallbackContext) -> int:
    """1-qadam: Kino qo'shish boshlash"""
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return ConversationHandler.END
    
    # Kategoriya tanlash tugmalari
    buttons = []
    row = []
    
    for i, (code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"admin_cat_{code}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("❌ BEKOR QILISH", callback_data="admin_cancel")])
    
    await update.message.reply_text(
        "🎬 <b>YANGI KINO QO'SHISH</b>\n\n"
        "1-qadam: Kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )
    
    return CATEGORY


async def add_movie_category(update: Update, context: CallbackContext) -> int:
    """2-qadam: Kategoriya tanlash"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "admin_cancel":
        await query.edit_message_text("❌ Kino qo'shish bekor qilindi.")
        return ConversationHandler.END
    
    category = query.data.replace("admin_cat_", "")
    context.user_data['new_movie_category'] = category
    
    category_emoji = CATEGORIES[category]['emoji']
    
    await query.edit_message_text(
        f"{category_emoji} <b>KINO QO'SHISH</b>\n\n"
        f"2-qadam: {category_emoji} {category.upper()} KODINI kiriting:\n"
        f"(masalan: 123)",
        parse_mode="HTML"
    )
    
    return CODE


async def add_movie_code(update: Update, context: CallbackContext) -> int:
    """3-qadam: Kod kiritish"""
    text = update.message.text.strip()
    
    try:
        code = int(text)
    except ValueError:
        await update.message.reply_text("❌ Kod raqam bo'lishi kerak! Qaytadan kiriting:")
        return CODE
    
    # Kod bandligini tekshirish
    existing = db.get_movie_by_code(code)
    if existing:
        await update.message.reply_text(
            f"❌ {code} kodli kino allaqachon mavjud!\n"
            f"Boshqa kod kiriting:"
        )
        return CODE
    
    context.user_data['new_movie_code'] = code
    
    await update.message.reply_text(
        f"✅ Kod qabul qilindi: {code}\n\n"
        f"3-qadam: KINO NOMINI kiriting:"
    )
    
    return NAME


async def add_movie_name(update: Update, context: CallbackContext) -> int:
    """4-qadam: Nom kiritish"""
    name = update.message.text.strip()
    context.user_data['new_movie_name'] = name
    
    await update.message.reply_text(
        f"✅ Nom qabul qilindi: {name}\n\n"
        f"4-qadam: VIDEO yuboring:"
    )
    
    return VIDEO


async def add_movie_video(update: Update, context: CallbackContext) -> int:
    """5-qadam: Video qabul qilish"""
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
    
    # Agar serial bo'lsa - qismlar sonini so'rash
    if category == "serial":
        await update.message.reply_text(
            f"✅ Video qabul qilindi!\n\n"
            f"5-qadam: NEÇÇA QISIMDAN IBORAT?\n"
            f"(raqam kiriting, masalan: 5)"
        )
        return PARTS_COUNT
    else:
        # Kino yoki multfilm bo'lsa - to'g'ridan-to'g'ri tavsifga
        await update.message.reply_text(
            f"✅ Video qabul qilindi!\n\n"
            f"5-qadam: TAVSIF kiriting:"
        )
        return DESCRIPTION


async def add_movie_parts_count(update: Update, context: CallbackContext) -> int:
    """6-qadam: Qismlar sonini qabul qilish (serial uchun)"""
    text = update.message.text.strip()
    
    try:
        parts_count = int(text)
    except ValueError:
        await update.message.reply_text("❌ Qismlar soni raqam bo'lishi kerak! Qaytadan kiriting:")
        return PARTS_COUNT
    
    context.user_data['new_movie_parts_count'] = parts_count
    
    await update.message.reply_text(
        f"✅ {parts_count} qismli serial\n\n"
        f"Endi har bir qism uchun VIDEO yuboring:\n"
        f"1-qism videosini yuboring:"
    )
    
    # Qismlar ro'yxatini yaratish
    context.user_data['new_movie_parts'] = []
    context.user_data['current_part'] = 1
    
    return VIDEO  # Qayta video qabul qilish uchun


async def add_movie_part_video(update: Update, context: CallbackContext) -> int:
    """Serial qismlari uchun video qabul qilish"""
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("❌ Iltimos, video yuboring!")
        return VIDEO
    
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
            f"Endi {current_part + 1}-qism videosini yuboring:"
        )
        return VIDEO
    else:
        # Barcha qismlar yig'ildi
        await update.message.reply_text(
            f"✅ Barcha {parts_count} qism qabul qilindi!\n\n"
            f"Endi TAVSIF kiriting:"
        )
        return DESCRIPTION


async def add_movie_description(update: Update, context: CallbackContext) -> int:
    """7-qadam: Tavsif kiritish va saqlash"""
    description = update.message.text.strip()
    
    # Ma'lumotlarni olish
    category = context.user_data['new_movie_category']
    code = context.user_data['new_movie_code']
    name = context.user_data['new_movie_name']
    
    # Kinoni saqlash
    if category == "serial" and 'new_movie_parts' in context.user_data:
        # Serial - qismlar bilan
        parts = context.user_data['new_movie_parts']
        success = db.add_serial(
            code=code,
            name=name,
            category=category,
            description=description,
            parts=parts
        )
        parts_text = f"{len(parts)} qism"
    else:
        # Kino yoki multfilm - bitta video
        file_id = context.user_data['new_movie_file_id']
        file_type = context.user_data['new_movie_file_type']
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
            f"✅ <b>KINO MUVOFFAQIYATLI QO'SHILDI!</b>\n\n"
            f"{category_emoji} Nomi: {name}\n"
            f"🔢 Kod: {code}\n"
            f"📂 Kategoriya: {category}\n"
            f"🎞 Qismlar: {parts_text}\n"
            f"📝 Tavsif: {description}"
        )
        
        buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
        
        await update.message.reply_text(
            result_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text("❌ Xatolik yuz berdi! Kino qo'shilmadi.")
    
    # Ma'lumotlarni tozalash
    context.user_data.clear()
    
    return ConversationHandler.END


# ==================== /DELETE - KINO O'CHIRISH ====================
async def delete_movie_start(update: Update, context: CallbackContext) -> None:
    """Kino o'chirish boshlash"""
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return
    
    # Kategoriya tanlash tugmalari
    buttons = []
    row = []
    
    for i, (code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"delete_cat_{code}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    await update.message.reply_text(
        "🗑 <b>KINO O'CHIRISH</b>\n\n"
        "Kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def delete_movie_category(update: Update, context: CallbackContext) -> None:
    """Kategoriya tanlanganda"""
    query = update.callback_query
    await query.answer()
    
    category = query.data.replace("delete_cat_", "")
    context.user_data['delete_category'] = category
    
    category_emoji = CATEGORIES[category]['emoji']
    
    await query.edit_message_text(
        f"{category_emoji} <b>{category.upper()} O'CHIRISH</b>\n\n"
        f"O'chirmoqchi bo'lgan {category} KODINI kiriting:",
        parse_mode="HTML"
    )


async def delete_movie_code(update: Update, context: CallbackContext) -> None:
    """Kod kiritilganda"""
    try:
        code = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Kod raqam bo'lishi kerak! Qaytadan kiriting:")
        return
    
    category = context.user_data.get('delete_category')
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await update.message.reply_text(
            f"❌ {code} kodli kino topilmadi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 QAYTISH", callback_data="back_to_admin_delete")
            ]])
        )
        return
    
    if movie['category'] != category:
        category_emoji = CATEGORIES[movie['category']]['emoji']
        await update.message.reply_text(
            f"❌ Bu kod {category_emoji} {movie['category']} kategoriyasiga tegishli!\n"
            f"Siz {CATEGORIES[category]['emoji']} {category} tanlagansiz.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 QAYTISH", callback_data="back_to_admin_delete")
            ]])
        )
        return
    
    # Kino topildi - tasdiqlash
    parts_count = len(movie.get('parts', [1]))
    parts_text = f"{parts_count} qism" if parts_count > 1 else "1 qism"
    
    text = (
        f"📌 <b>KINO TOPILDI:</b>\n\n"
        f"{CATEGORIES[category]['emoji']} Nomi: {movie['name']}\n"
        f"🔢 Kod: {code}\n"
        f"🎞 Qismlar: {parts_text}\n\n"
        f"⚠️ <b>O'chirishni tasdiqlaysizmi?</b>"
    )
    
    buttons = [
        [
            InlineKeyboardButton("✅ HA", callback_data=f"confirm_yes_{code}"),
            InlineKeyboardButton("❌ YO'Q", callback_data=f"confirm_no_{code}")
        ],
        [InlineKeyboardButton("🔙 QAYTISH", callback_data="back_to_admin_delete")]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def admin_delete_execute(query, context: CallbackContext, code: int) -> None:
    """Kino o'chirishni amalga oshirish"""
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await query.edit_message_text(
            f"❌ {code} kodli kino topilmadi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    success = db.delete_movie(code)
    
    if success:
        await query.edit_message_text(
            f"✅ <b>KINO O'CHIRILDI!</b>\n\n"
            f"{CATEGORIES[movie['category']]['emoji']} {movie['name']} (Kod: {code})",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]]),
            parse_mode="HTML"
        )
    else:
        await query.edit_message_text(
            f"❌ Xatolik yuz berdi! Kino o'chirilmadi.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )


async def back_to_admin_delete(update: Update, context: CallbackContext) -> None:
    """Admin o'chirishga qaytish"""
    query = update.callback_query
    await query.answer()
    
    buttons = []
    row = []
    
    for i, (code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"delete_cat_{code}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    await query.edit_message_text(
        "🗑 <b>KINO O'CHIRISH</b>\n\n"
        "Kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


# ==================== /SEND - XABAR YUBORISH ====================
async def send_message_start(update: Update, context: CallbackContext) -> None:
    """Xabar yuborish boshlash"""
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "📝 <b>XABAR YUBORISH</b>\n\n"
            "Ishlatish: /send <xabar matni>\n\n"
            "Misol: /send Yangi kino Avatar qo'shildi!",
            parse_mode="HTML"
        )
        return
    
    message = ' '.join(context.args)
    context.user_data['broadcast_message'] = message
    
    # Tasdiqlash
    users_count = len(db.get_all_users())
    
    text = (
        f"📝 <b>XABAR YUBORISH</b>\n\n"
        f"Xabar: {message}\n"
        f"👥 Qabul qiluvchilar: {users_count} ta foydalanuvchi\n\n"
        f"Yuborishni tasdiqlaysizmi?"
    )
    
    buttons = [
        [
            InlineKeyboardButton("✅ HA", callback_data="broadcast_confirm"),
            InlineKeyboardButton("❌ YO'Q", callback_data="broadcast_cancel")
        ]
    ]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def broadcast_confirm(update: Update, context: CallbackContext) -> None:
    """Xabar yuborishni tasdiqlash"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "broadcast_cancel":
        await query.edit_message_text("❌ Xabar yuborish bekor qilindi.")
        return
    
    message = context.user_data.get('broadcast_message')
    users = db.get_all_users()
    
    await query.edit_message_text(
        f"📤 Xabar yuborilmoqda... ({len(users)} ta foydalanuvchi)"
    )
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            await context.bot.send_message(
                chat_id=int(user['user_id']),
                text=message,
                parse_mode="HTML"
            )
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"Xabar yuborishda xatolik {user['user_id']}: {e}")
    
    result_text = (
        f"📊 <b>XABAR YUBORISH NATIJASI</b>\n\n"
        f"✅ Yuborildi: {sent} ta\n"
        f"❌ Yuborilmadi: {failed} ta\n"
        f"📈 Jami: {len(users)} ta"
    )
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await query.edit_message_text(
        result_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )
    
    context.user_data.clear()


# ==================== /STATS - STATISTIKA ====================
async def stats_command(update: Update, context: CallbackContext) -> None:
    """Bot statistikasi"""
    if not await is_admin(update):
        await update.message.reply_text("❌ Bu buyruq faqat admin uchun!")
        return
    
    users = db.get_all_users()
    movies = db.get_all_movies()
    
    # Kategoriya bo'yicha kinolar soni
    movies_by_category = {
        'kino': 0,
        'serial': 0,
        'multfilm': 0
    }
    
    for movie in movies:
        cat = movie.get('category', 'kino')
        if cat in movies_by_category:
            movies_by_category[cat] += 1
    
    # Oxirgi 24 soatdagi foydalanuvchilar
    from datetime import datetime, timedelta
    yesterday = datetime.now() - timedelta(days=1)
    new_users_today = 0
    # Bu qism database funksiyasi bilan to'ldiriladi
    
    text = (
        f"📊 <b>BOT STATISTIKASI</b>\n\n"
        f"👥 <b>FOYDALANUVCHILAR:</b>\n"
        f"├─ Jami: {len(users)} ta\n"
        f"└─ Oxirgi 24 soat: +{new_users_today} ta\n\n"
        
        f"🎬 <b>KINOLAR:</b>\n"
        f"├─ Jami: {len(movies)} ta\n"
        f"├─ 🎬 Kino: {movies_by_category['kino']} ta\n"
        f"├─ 📺 Serial: {movies_by_category['serial']} ta\n"
        f"└─ 🐰 Multfilm: {movies_by_category['multfilm']} ta"
    )
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


# ==================== /CANCEL - BEKOR QILISH ====================
async def cancel(update: Update, context: CallbackContext) -> int:
    """Jarayonni bekor qilish"""
    await update.message.reply_text("❌ Jarayon bekor qilindi.")
    context.user_data.clear()
    return ConversationHandler.END


# ==================== HANDLERLAR ====================
# Add movie conversation handler
add_movie_conv = ConversationHandler(
    entry_points=[CommandHandler("addmovie", add_movie_start)],
    states={
        CATEGORY: [CallbackQueryHandler(add_movie_category, pattern="^admin_")],
        CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_code)],
        NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_name)],
        VIDEO: [
            MessageHandler(filters.VIDEO, add_movie_video),
            MessageHandler(filters.Document.ALL, add_movie_video)
        ],
        PARTS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_parts_count)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_description)],
    },
    fallbacks=[CommandHandler("cancel", cancel)]
)

# Delete handlers
delete_category_handler = CallbackQueryHandler(delete_movie_category, pattern="^delete_cat_")
delete_code_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, delete_movie_code)
back_to_delete_handler = CallbackQueryHandler(back_to_admin_delete, pattern="^back_to_admin_delete$")

# Broadcast handlers
broadcast_handler = CallbackQueryHandler(broadcast_confirm, pattern="^broadcast_")

# Other 
