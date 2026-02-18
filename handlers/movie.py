import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, MessageHandler, filters
from database import db
from config import CATEGORIES

logger = logging.getLogger(__name__)


# ==================== KATEGORIYA TANLASH ====================
async def category_handler(update: Update, context: CallbackContext):
    """Kategoriya tanlanganda"""
    query = update.callback_query
    if not query.message:
        return

    category = query.data.replace("cat_", "")
    context.user_data['current_category'] = category
    
    category_name = CATEGORIES[category]['name']
    category_emoji = CATEGORIES[category]['emoji']
    
    buttons = [
        [InlineKeyboardButton(f"📋 {category_name}LAR RO'YXATI", callback_data=f"list_{category}")],
        [InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        f"{category_emoji} <b>{category_name} QIDIRISH</b>\n\n"
        f"<b>Kod kiriting</b> (masalan: 123):",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


# ==================== KINO QIDIRISH ====================
async def search_movie(update: Update, context: CallbackContext):
    """Foydalanuvchi matn yozganda - kino qidirish"""
    if not update.message or not update.message.text:
        return
        
    text = update.message.text.strip()
    category = context.user_data.get('current_category')
    
    if not category:
        await update.message.reply_text(
            "❌ Avval kategoriya tanlang! /start",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])        )
        return
    
    try:
        code = int(text)
        await search_by_code(update, context, code, category)
    except ValueError:
        await search_by_name(update, context, text, category)


async def search_by_code(update: Update, context: CallbackContext, code: int, category: str):
    """Kod orqali qidirish"""
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await update.message.reply_text(
            f"❌ {code} kodli kino topilmadi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    if movie['category'] != category:
        await update.message.reply_text(
            f"❌ Bu kod {movie['category']} kategoriyasiga tegishli!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    await show_movie(update, context, movie)


async def search_by_name(update: Update, context: CallbackContext, name: str, category: str):
    """Nom orqali qidirish"""
    movies = db.search_movies_by_name(name, category)
    
    if not movies:
        await update.message.reply_text(
            f"❌ '{name}' nomli kino topilmadi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    if len(movies) == 1:
        await show_movie(update, context, movies[0])    
    else:
        text = f"🔍 '{name}' bo'yicha {len(movies)} ta natija:\n\n"
        for m in movies[:10]:
            parts = len(m.get('parts', [1]))
            text += f"🎬 {m['code']}. {m['name']} ({parts} qism)\n"
        
        text += "\nKodni kiriting:"
        
        await update.message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )


# ==================== KINO KO'RSATISH ====================
async def show_movie(update: Update, context: CallbackContext, movie: dict):
    """Kinoni ko'rsatish"""
    parts = movie.get('parts', [])
    
    if len(parts) > 1:
        await show_serial_parts(update, context, movie)
        return
    
    file_id = movie.get('file_id') or (parts[0]['file_id'] if parts else None)
    
    if not file_id:
        await update.message.reply_text("❌ Video topilmadi!")
        return
    
    caption = (
        f"{CATEGORIES[movie['category']]['emoji']} <b>{movie['name']}</b>\n"
        f"🔢 Kod: {movie['code']}\n"
        f"📝 {movie['description']}"
    )
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    try:
        if movie.get('file_type') == 'video':
            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        else:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
    except Exception as e:
        logger.error(f"Video yuborishda xatolik: {e}")
        await update.message.reply_text("❌ Xatolik yuz berdi!")


async def show_serial_parts(update: Update, context: CallbackContext, movie: dict):
    """Serial qismlarini ko'rsatish"""
    parts = movie.get('parts', [])
    emoji = CATEGORIES[movie['category']]['emoji']
    
    text = (
        f"{emoji} <b>{movie['name']}</b>\n"
        f"🔢 Kod: {movie['code']}\n"
        f"🎞 Qismlar: {len(parts)} ta\n"
        f"📝 {movie['description']}\n\n"
        f"👇 Qismni tanlang:"
    )
    
    buttons = []
    row = []
    
    for i, part in enumerate(parts, 1):
        row.append(InlineKeyboardButton(
            f"🎬 {part.get('name', f'{i}-qism')}",
            callback_data=f"part_{movie['code']}_{i}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def send_part(update: Update, context: CallbackContext, code: int, part_index: int):
    """Serial qismini yuborish"""
    query = update.callback_query
    if not query.message:
        return

    movie = db.get_movie_by_code(code)
    
    if not movie:
        await query.edit_message_text("❌ Kino topilmadi!")
        return
    
    parts = movie.get('parts', [])
    real_index = part_index - 1
    
    if real_index >= len(parts) or real_index < 0:
        await query.edit_message_text("❌ Qism topilmadi!")
        return
    
    part = parts[real_index]
    file_id = part.get('file_id')
    
    if not file_id:
        await query.edit_message_text("❌ Video topilmadi!")
        return
    
    caption = (
        f"{CATEGORIES[movie['category']]['emoji']} <b>{movie['name']} - {part.get('name', f'{part_index}-qism')}</b>\n"
        f"🔢 Kod: {movie['code']}"
    )
    
    buttons = [[
        InlineKeyboardButton("🔙 QISMLAR", callback_data=f"parts_{code}"),
        InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
    ]]
    
    try:
        await context.bot.send_video(
            chat_id=query.message.chat_id,
            video=file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    except Exception as e:
        logger.error(f"Video yuborishda xatolik: {e}")
        await query.edit_message_text("❌ Xatolik yuz berdi!")


async def show_parts(update: Update, context: CallbackContext, code: int):
    """Serial qismlarini qayta ko'rsatish"""
    query = update.callback_query
    if not query.message:
        return

    movie = db.get_movie_by_code(code)
    
    if not movie:
        await query.edit_message_text("❌ Kino topilmadi!")
        return
    
    parts = movie.get('parts', [])
    emoji = CATEGORIES[movie['category']]['emoji']
    
    text = (
        f"{emoji} <b>{movie['name']}</b>\n"
        f"🔢 Kod: {movie['code']}\n"
        f"🎞 Qismlar: {len(parts)} ta\n\n"
        f"👇 Qismni tanlang:"
    )
    
    buttons = []
    row = []
    
    for i, part in enumerate(parts, 1):
        row.append(InlineKeyboardButton(
            f"🎬 {part.get('name', f'{i}-qism')}",
            callback_data=f"part_{code}_{i}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


# ==================== KINOLAR RO'YXATI ====================
async def show_movielist(update: Update, context: CallbackContext):
    """Barcha kinolar ro'yxati"""
    query = update.callback_query
    if not query.message:
        return
    
    movies = db.get_all_movies()
    
    if not movies:
        await query.edit_message_text(
            "📋 Kinolar ro'yxati bo'sh",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    text = f"📋 <b>KINOLAR RO'YXATI ({len(movies)} ta)</b>\n\n"
    
    for cat in ['kino', 'serial', 'multfilm']:
        cat_movies = [m for m in movies if m['category'] == cat]
        if cat_movies:
            emoji = CATEGORIES[cat]['emoji']
            text += f"{emoji} <b>{cat.upper()}</b>\n"
            for m in cat_movies[:5]:
                parts = len(m.get('parts', [1]))
                text += f"  ├─ {m['code']}. {m['name']} ({parts} qism)\n"
            if len(cat_movies) > 5:
                text += f"  └─ ... va yana {len(cat_movies)-5} ta\n"
            text += "\n"
    
    text += "Kodni kiriting:"
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
        ]]),
        parse_mode="HTML"
    )


async def show_category_movielist(update: Update, context: CallbackContext):
    """Kategoriya bo'yicha kinolar ro'yxati"""
    query = update.callback_query
    if not query.message:
        return

    category = query.data.replace("list_", "")
    
    movies = db.get_movies_by_category(category)
    emoji = CATEGORIES[category]['emoji']
    
    if not movies:
        await query.edit_message_text(
            f"{emoji} {category} kategoriyasida kinolar yo'q",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    text = f"{emoji} <b>{category.upper()}LAR ({len(movies)} ta)</b>\n\n"
    
    for movie in movies[:20]:
        parts = len(movie.get('parts', [1]))
        text += f"🎬 {movie['code']}. {movie['name']} ({parts} qism)\n"
    
    if len(movies) > 20:
        text += f"\n... va yana {len(movies)-20} ta"
    
    text += f"\n\nKodni kiriting:"
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
        ]]),
        parse_mode="HTML"
    )


# ==================== SAHIFALASH (Kelajak uchun) ====================
async def show_movielist_page(update: Update, context: CallbackContext, page: int):
    """Sahifalangan ro'yxat"""
    pass

async def show_category_page(update: Update, context: CallbackContext, category: str, page: int):
    """Kategoriya sahifasi"""
    pass


# ==================== ENG MUHIM QISM: EXPORT HANDLER ====================
# Bu qator hech qanday funksiya ichida emas, chapdan to'g'ridan-to'g'ri boshlanadi.
search_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie)
