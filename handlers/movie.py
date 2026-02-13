import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from database import db
from config import CATEGORIES

logger = logging.getLogger(__name__)


async def search_movie(update: Update, context: CallbackContext) -> None:
    """Foydalanuvchi matn yozganda - kino qidirish"""
    user_input = update.message.text.strip()
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    
    # Kategoriya tanlanganmi?
    category = context.user_data.get('current_category')
    
    if not category:
        await update.message.reply_text(
            "❌ Avval kategoriya tanlang! /start",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    logger.info(f"🔍 Qidiruv: {user_input} ({category}) - {user_name}")
    
    # Kod orqali qidirish
    try:
        code = int(user_input)
        await search_by_code(update, context, code, category)
    except ValueError:
        # Agar son bo'lmasa - nom orqali qidirish
        await search_by_name(update, context, user_input, category)


async def search_by_code(update: Update, context: CallbackContext, code: int, category: str):
    """Kod orqali kino qidirish"""
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await update.message.reply_text(
            f"❌ {code} kodli kino topilmadi!",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    # Kategoriya mosligini tekshirish
    if movie['category'] != category:
        category_emoji = CATEGORIES[movie['category']]['emoji']
        await update.message.reply_text(
            f"❌ Bu kod {category_emoji} {movie['category']} kategoriyasiga tegishli.\n"
            f"Siz {CATEGORIES[category]['emoji']} {category} kategoriyasini tanlagansiz.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    # Kino topildi
    await show_movie(update, context, movie)


async def search_by_name(update: Update, context: CallbackContext, name: str, category: str):
    """Nom orqali kino qidirish"""
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
        # Bitta kino topilsa - ko'rsatish
        await show_movie(update, context, movies[0])
    else:
        # Bir nechta kino topilsa - ro'yxat
        await show_search_results(update, context, movies, name, category)


async def show_movie(update: Update, context: CallbackContext, movie: dict):
    """Kinoni ko'rsatish"""
    category = movie['category']
    category_emoji = CATEGORIES[category]['emoji']
    parts = movie.get('parts', [])
    parts_count = len(parts)
    
    # Agar serial bo'lsa - qismlar ro'yxati
    if parts_count > 1:
        await show_serial_parts(update, context, movie)
        return
    
    # Agar kino bo'lsa - videoni yuborish
    file_id = movie.get('file_id') or (parts[0]['file_id'] if parts else None)
    
    if not file_id:
        await update.message.reply_text("❌ Video topilmadi!")
        return
    
    # Video yuborish
    caption = (
        f"{category_emoji} <b>{movie['name']}</b>\n"
        f"🔢 Kod: {movie['code']}\n"
        f"📂 Kategoriya: {category}\n"
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
        await update.message.reply_text(
            "❌ Video yuborishda xatolik yuz berdi.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


async def show_serial_parts(update: Update, context: CallbackContext, movie: dict):
    """Serial qismlarini ko'rsatish"""
    category_emoji = CATEGORIES[movie['category']]['emoji']
    parts = movie.get('parts', [])
    
    text = (
        f"{category_emoji} <b>{movie['name']}</b>\n"
        f"🔢 Kod: {movie['code']}\n"
        f"📂 Kategoriya: {movie['category']}\n"
        f"🎞 Qismlar: {len(parts)} ta\n"
        f"📝 {movie['description']}\n\n"
        f"👇 <b>Qismni tanlang:</b>"
    )
    
    # Qismlar uchun tugmalar
    buttons = []
    row = []
    
    for i, part in enumerate(parts, 1):
        part_name = part.get('name', f"{i}-qism")
        row.append(InlineKeyboardButton(
            f"🎬 {part_name}",
            callback_data=f"part_{movie['code']}_{i}"
        ))
        if i % 2 == 0:  # Har 2 tadan qator
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([
        InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
    ])
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def send_part(query, context: CallbackContext, code: int, part_index: int):
    """Serial qismini yuborish"""
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await query.edit_message_text("❌ Kino topilmadi!")
        return
    
    parts = movie.get('parts', [])
    
    if part_index >= len(parts):
        await query.edit_message_text("❌ Qism topilmadi!")
        return
    
    part = parts[part_index]
    part_name = part.get('name', f"{part_index+1}-qism")
    file_id = part.get('file_id')
    
    if not file_id:
        await query.edit_message_text("❌ Video topilmadi!")
        return
    
    category_emoji = CATEGORIES[movie['category']]['emoji']
    
    caption = (
        f"{category_emoji} <b>{movie['name']} - {part_name}</b>\n"
        f"🔢 Kod: {movie['code']}\n"
        f"📂 Kategoriya: {movie['category']}\n"
        f"📝 {movie['description']}"
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
        await query.edit_message_text(
            "❌ Video yuborishda xatolik yuz berdi.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


async def show_parts(query, context: CallbackContext, code: int):
    """Serial qismlarini ko'rsatish (callback uchun)"""
    movie = db.get_movie_by_code(code)
    
    if not movie:
        await query.edit_message_text("❌ Kino topilmadi!")
        return
    
    category_emoji = CATEGORIES[movie['category']]['emoji']
    parts = movie.get('parts', [])
    
    text = (
        f"{category_emoji} <b>{movie['name']}</b>\n"
        f"🔢 Kod: {movie['code']}\n"
        f"🎞 Qismlar: {len(parts)} ta\n\n"
        f"👇 <b>Qismni tanlang:</b>"
    )
    
    # Qismlar uchun tugmalar
    buttons = []
    row = []
    
    for i, part in enumerate(parts, 1):
        part_name = part.get('name', f"{i}-qism")
        row.append(InlineKeyboardButton(
            f"🎬 {part_name}",
            callback_data=f"part_{movie['code']}_{i}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([
        InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def show_search_results(update: Update, context: CallbackContext, movies: list, search_term: str, category: str):
    """Qidiruv natijalarini ko'rsatish"""
    category_emoji = CATEGORIES[category]['emoji']
    
    text = (
        f"🔍 <b>'{search_term}' bo'yicha {len(movies)} ta natija:</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
    )
    
    for movie in movies:
        parts_count = len(movie.get('parts', [1]))
        parts_text = f" ({parts_count} qism)" if parts_count > 1 else ""
        text += f"🎬 {movie['code']}. {movie['name']}{parts_text}\n"
    
    text += f"\n👇 <b>Kodni kiriting:</b>"
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await update.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def show_movielist(query, context: CallbackContext):
    """Barcha kinolar ro'yxatini ko'rsatish"""
    all_movies = db.get_all_movies()
    
    if not all_movies:
        await query.edit_message_text(
            "📋 Kinolar ro'yxati bo'sh.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
        return
    
    # Kategoriya bo'yicha guruhlash
    movies_by_category = {
        'kino': [],
        'serial': [],
        'multfilm': []
    }
    
    for movie in all_movies:
        cat = movie.get('category', 'kino')
        if cat in movies_by_category:
            movies_by_category[cat].append(movie)
    
    text = f"📋 <b>KINOLAR RO'YXATI ({len(all_movies)} ta)</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for category, movies in movies_by_category.items():
        if movies:
            emoji = CATEGORIES[category]['emoji']
            text += f"\n{emoji} <b>{category.upper()}</b>\n"
            
            for movie in movies[:10]:  # Har bir kategoriyadan 10 tadan
                parts_count = len(movie.get('parts', [1]))
                parts_text = f" ({parts_count} qism)" if parts_count > 1 else ""
                text += f"  ├─ {movie['code']}. {movie['name']}{parts_text}\n"
            
            if len(movies) > 10:
                text += f"  └─ ... va yana {len(movies)-10} ta\n"
    
    text += f"\n👇 <b>Kodni kiriting:</b>"
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
    )


async def get_movie_by_code_handler(update: Update, context: CallbackContext):
    """Faqat kod orqali kino olish (callback uchun)"""
    # Bu funksiya callback.py dan chaqiriladi
    pass


# Handlerlar
search_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, search_movie)
