import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CallbackContext, ConversationHandler, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from config import ADMIN_ID, CATEGORIES
from database import db

logger = logging.getLogger(__name__)

# Conversation bosqichlari
VIDEO, NAME, CODE, CATEGORY, PARTS_COUNT, PART_VIDEOS, DESCRIPTION = range(7)
CHANNEL_ADD, CHANNEL_DEL = range(7, 9)

### ------- Yordamchi funksiya: Admin ekanini tekshirish ------- ###
async def is_admin(update: Update) -> bool:
    return update.effective_user.id == ADMIN_ID

### =========== KINO QO‘SHISH =========== ###
async def start_add_movie_conv(update: Update, context: CallbackContext) -> int:
    if not await is_admin(update):
        await update.effective_message.reply_text("❌ Faqat admin uchun!")
        return ConversationHandler.END
    await update.effective_message.reply_text(
        "🎬 Yangi kino yoki serial qo‘shish!\n1️⃣ Video yoki hujjat yuboring:"
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
        await update.message.reply_text("❌ Video yoki dokument yuboring!")
        return VIDEO
    context.user_data['file_id'] = file_id
    context.user_data['file_type'] = file_type
    await update.message.reply_text("2️⃣ Kino yoki serial nomini kiriting:")
    return NAME

async def add_movie_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text.strip()
    await update.message.reply_text("3️⃣ Kino kodi (raqam) ni kiriting:")
    return CODE

async def add_movie_code(update: Update, context: CallbackContext) -> int:
    try:
        code = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Kod faqat raqam!")
        return CODE
    if db.get_movie_by_code(code):
        await update.message.reply_text("❌ Bunday kodli kino allaqachon mavjud!")
        return CODE
    context.user_data['code'] = code

    buttons = []
    row = []
    for i, (cat_code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(f"{cat['emoji']} {cat['name']}", callback_data=f"cat_{cat_code}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row: buttons.append(row)

    await update.message.reply_text(
        "4️⃣ Kategoriyani tanlang:", 
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATEGORY

async def add_movie_category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.replace("cat_", "")
    context.user_data['category'] = category

    if category == "serial":
        await query.edit_message_text("5️⃣ Serial necha qismdan iborat?")
        return PARTS_COUNT
    else:
        await query.edit_message_text("5️⃣ Tavsif kiriting:")
        return DESCRIPTION

async def add_movie_parts_count(update: Update, context: CallbackContext) -> int:
    try:
        parts_count = int(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("❌ Raqam kiriting!")
        return PARTS_COUNT
    context.user_data['parts_count'] = parts_count
    context.user_data['parts'] = []
    context.user_data['current_part'] = 1
    await update.message.reply_text(f"1-qism videosini yuboring:")
    return PART_VIDEOS

async def add_movie_part_video(update: Update, context: CallbackContext) -> int:
    if update.message.video:
        file_id = update.message.video.file_id
    elif update.message.document:
        file_id = update.message.document.file_id
    else:
        await update.message.reply_text("❌ Video yoki dokument yuboring!")
        return PART_VIDEOS

    part_idx = context.user_data['current_part']
    parts = context.user_data['parts']
    parts.append({'name': f"{part_idx}-qism", 'file_id': file_id})
    context.user_data['parts'] = parts

    if part_idx < context.user_data['parts_count']:
        context.user_data['current_part'] = part_idx + 1
        await update.message.reply_text(f"{part_idx + 1}-qism videosini yuboring:")
        return PART_VIDEOS
    else:
        await update.message.reply_text("5️⃣ Tavsif kiriting:")
        return DESCRIPTION

async def add_movie_description(update: Update, context: CallbackContext) -> int:
    description = update.message.text.strip()
    code = context.user_data['code']
    name = context.user_data['name']
    category = context.user_data['category']
    file_type = context.user_data.get('file_type', 'video')

    if category == "serial":
        success = db.add_serial(
            code, name, category, description, context.user_data['parts']
        )
        parts_text = f"{len(context.user_data['parts'])} qism"
    else:
        file_id = context.user_data['file_id']
        success = db.add_movie(
            code, name, category, description, file_id=file_id, file_type=file_type
        )
        parts_text = "1 qism"

    if success:
        msg = f"✅ Saqlandi! {CATEGORIES[category]['emoji']} {name}\n🔢 Kod: {code}\n🎞 {parts_text}\n📝 {description}"
        await update.message.reply_text(
            msg, reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_to_main")]]
            )
        )
    else:
        await update.message.reply_text("❌ Xatolik!")
    context.user_data.clear()
    return ConversationHandler.END

### ========== KINO O‘CHIRISH ========== ###
async def start_delete_movie_conv(update: Update, context: CallbackContext) -> int:
    if not await is_admin(update):
        await update.effective_message.reply_text("❌ Faqat admin uchun!")
        return ConversationHandler.END
    buttons = []
    row = []
    for i, (cat_code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(f"{cat['emoji']} {cat['name']}", callback_data=f"delcat_{cat_code}"))
        if i % 2 == 0: buttons.append(row); row=[]
    if row: buttons.append(row)
    await update.effective_message.reply_text(
        "🗑 O‘chirish uchun kategoriyani tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return CATEGORY

async def delete_movie_category(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    await query.answer()
    category = query.data.replace("delcat_", "")
    context.user_data['delete_category'] = category
    await query.edit_message_text("2️⃣ O‘chirish uchun kod kiriting:")
    return CODE

async def delete_movie_code(update: Update, context: CallbackContext) -> int:
    code = update.message.text.strip()
    try:
        code = int(code)
    except ValueError:
        await update.message.reply_text("❌ Kod faqat raqam!")
        return CODE
    movie = db.get_movie_by_code(code)
    if not movie:
        await update.message.reply_text("❌ Bunday kodli kino topilmadi!")
        return CODE
    if movie['category'] != context.user_data['delete_category']:
        await update.message.reply_text("❌ Bu kod boshqa kategoriya uchun!")
        return CODE
    parts_count = len(movie.get('parts', [1]))
    msg = (
        f"TOPILDI:\n{CATEGORIES[movie['category']]['emoji']} {movie['name']}\n"
        f"🔢 Kod: {code}\n🎞 {parts_count} qism\n"
        f"O‘chirishni tasdiqlaysizmi?"
    )
    buttons = [
        [InlineKeyboardButton("✅ Ha", callback_data=f"confirm_del_{code}")],
        [InlineKeyboardButton("🏠 Ortga", callback_data="admin_panel")]
    ]
    await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(buttons))
    return ConversationHandler.END

async def confirm_delete_movie(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    code = int(query.data.replace("confirm_del_", ""))
    movie = db.get_movie_by_code(code)
    if not movie:
        await query.edit_message_text("❌ Kino topilmadi!")
        return
    success = db.delete_movie(code)
    if success:
        await query.edit_message_text(
            f"✅ O‘chirildi: {CATEGORIES[movie['category']]['emoji']} {movie['name']}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_to_main")]]
            )
        )
    else:
        await query.edit_message_text("❌ Xatolik!")

### ========== STATISTIKA ========== ###
async def show_stats(update: Update, context: CallbackContext) -> None:
    users = db.get_all_users()
    movies = db.get_all_movies()
    by_cat = {"kino": 0, "serial": 0, "multfilm": 0}
    for movie in movies:
        c = movie.get('category', 'kino')
        if c in by_cat: by_cat[c] += 1
    text = (
        f"📊 STATISTIKA\n\n"
        f"👥 Foydalanuvchilar: {len(users)}\n"
        f"🎬 Kinolar: {len(movies)}\n"
        f"    Kino: {by_cat['kino']}\n"
        f"    Serial: {by_cat['serial']}\n"
        f"    Multfilm: {by_cat['multfilm']}"
    )
    await update.callback_query.edit_message_text(
        text, 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_to_main")]])
    )

### ========== XABAR YUBORISH ========== ###
async def input_broadcast(update: Update, context: CallbackContext) -> None:
    await update.callback_query.edit_message_text(
        "📢 Yangi xabar matnini, rasm, video yoki faylni yuboring:"
    )
    context.user_data['broadcast'] = {}
    return

async def handle_broadcast(update: Update, context: CallbackContext) -> None:
    # Matn, media, yoki document
    msg = update.message
    broadcast = context.user_data['broadcast']
    if msg.text:
        broadcast['text'] = msg.text
    if msg.photo:
        broadcast['photo'] = msg.photo[-1].file_id
    if msg.video:
        broadcast['video'] = msg.video.file_id
    if msg.document:
        broadcast['document'] = msg.document.file_id
    # Tasdiqlash menyu
    buttons = [
        [InlineKeyboardButton("✅ Yuborish", callback_data="do_broadcast")],
        [InlineKeyboardButton("❌ Bekor qilish", callback_data="admin_panel")]
    ]
    await msg.reply_text("Yuborishni tasdiqlaysizmi?", reply_markup=InlineKeyboardMarkup(buttons))

async def do_broadcast(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    users = db.get_all_users()
    broadcast = context.user_data.get('broadcast', {})
    sent, failed = 0, 0
    for user in users:
        kwargs = dict(chat_id=int(user['user_id']))
        try:
            if broadcast.get('text') and broadcast.get('photo'):
                await context.bot.send_photo(**kwargs, photo=broadcast['photo'], caption=broadcast['text'])
            elif broadcast.get('text') and broadcast.get('video'):
                await context.bot.send_video(**kwargs, video=broadcast['video'], caption=broadcast['text'])
            elif broadcast.get('text') and broadcast.get('document'):
                await context.bot.send_document(**kwargs, document=broadcast['document'], caption=broadcast['text'])
            elif broadcast.get('photo'):
                await context.bot.send_photo(**kwargs, photo=broadcast['photo'])
            elif broadcast.get('video'):
                await context.bot.send_video(**kwargs, video=broadcast['video'])
            elif broadcast.get('document'):
                await context.bot.send_document(**kwargs, document=broadcast['document'])
            elif broadcast.get('text'):
                await context.bot.send_message(**kwargs, text=broadcast['text'])
            sent += 1
        except Exception as e:
            failed += 1
            logger.error(f"Foydalanuvchiga yubora olmadi: {user['user_id']} - {e}")

    await query.edit_message_text(
        f"📢 Yuborildi: {sent} ta\n❌ Yuborilmadi: {failed} ta",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Asosiy menyu", callback_data="back_to_main")]])
    )
    context.user_data.pop('broadcast', None)

### ========== HANDLERLAR ========== ###
add_movie_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_add_movie_conv, pattern="add_movie")],
    states={
        VIDEO: [MessageHandler(filters.VIDEO | filters.Document.ALL, add_movie_video)],
        NAME:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_name)],
        CODE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_code)],
        CATEGORY: [CallbackQueryHandler(add_movie_category, pattern="^cat_")],
        PARTS_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_parts_count)],
        PART_VIDEOS: [MessageHandler(filters.VIDEO | filters.Document.ALL, add_movie_part_video)],
        DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_movie_description)],
    },
    fallbacks=[],
    per_message=False,
)

delete_movie_conv = ConversationHandler(
    entry_points=[CallbackQueryHandler(start_delete_movie_conv, pattern="delete_movie")],
    states={
        CATEGORY: [CallbackQueryHandler(delete_movie_category, pattern="^delcat_")],
        CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_movie_code)],
    },
    fallbacks=[],
    per_message=False,
)

confirm_delete_handler = CallbackQueryHandler(confirm_delete_movie, pattern="^confirm_del_")
send_handler = CallbackQueryHandler(input_broadcast, pattern="send_broadcast")
broadcast_handler = MessageHandler(filters.ALL, handle_broadcast)
do_broadcast_handler = CallbackQueryHandler(do_broadcast, pattern="do_broadcast")

# Statistika
stats_handler = CallbackQueryHandler(show_stats, pattern="^stats$")
