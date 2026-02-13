import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext
from handlers.start import check_subscription, show_main_menu
from handlers.movie import show_movielist, show_movie_by_code, show_parts
from config import CATEGORIES

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, context: CallbackContext) -> None:
    """BARCHA TUGMALAR - asosiy callback handler"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user_id = update.effective_user.id
    user_name = update.effective_user.full_name
    
    logger.info(f"🔘 Tugma bosildi: {data} - {user_name} ({user_id})")
    
    # ==================== OBUNA TEKSHIRISH ====================
    if data == "check_subscription":
        is_subscribed, _, channels_info = await check_subscription(update, context)
        
        if is_subscribed:
            # Obuna bo'lgan - asosiy menyuga
            await query.edit_message_text(
                f"✅ Obuna tasdiqlandi! /start ni bosing."
            )
        else:
            # Hali ham obuna emas
            await query.answer(
                "❌ Hali ham obuna bo'lmagansiz! Kanallarga a'zo bo'ling.",
                show_alert=True
 )
    
    # ==================== ASOSIY MENYUGA QAYTISH ====================
    elif data == "back_to_main":
        await show_main_menu_callback(query, user_name)
    
    # ==================== KATEGORIYA TANLASH ====================
    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        context.user_data['current_category'] = category
        
        category_name = CATEGORIES[category]["name"]
        category_emoji = CATEGORIES[category]["emoji"]
        
        buttons = [
            [InlineKeyboardButton(f"📋 {category_name}LAR RO'YXATI", callback_data=f"list_{category}")],
            [InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]
        ]
        
        await query.edit_message_text(
            f"{category_emoji} <b>{category_name} QIDIRISH</b>\n\n"
            f"<b>{category_name} kodini kiriting</b> (masalan: 123)\n"
            f"yoki pastdagi tugmalardan foydalaning:",
            reply_markup=InlineKeyboardMarkup(buttons),
            parse_mode="HTML"
 )
    
    # ==================== KATEGORIYA BO'YICHA RO'YXAT ====================
    elif data.startswith("list_"):
        category = data.replace("list_", "")
        await show_movielist_by_category(query, context, category)
    
    # ==================== UMUMIY KINOLAR RO'YXATI ====================
    elif data == "show_movielist":
        await show_movielist(query, context)
    
    # ==================== RO'YXAT SAHIFALARI ====================
    elif data.startswith("page_"):
        # page_1, page_2, ...
        page = int(data.replace("page_", ""))
        await show_movielist_page(query, context, page)
    
    # ==================== KATEGORIYA RO'YXATI SAHIFALARI ====================
    elif data.startswith("catpage_"):
        # catpage_kino_1, catpage_serial_2, ...
        parts = data.split("_")
        category = parts[1]
        page = int(parts[2])
        await show_movielist_by_category_page(query, context, category, page)
    
    # ==================== SERIAL QISMLARI ====================
    elif data.startswith("parts_"):
        # parts_123 - 123 kodli serial qismlari
        code = int(data.replace("parts_", ""))
        await show_parts(query, context, code)
    
    # ==================== QISMNI KO'RSATISH ====================
    elif data.startswith("part_"):
        # part_123_2 - 123 kodli serialning 2-qismi
        parts = data.split("_")
        code = int(parts[1])
        part_index = int(parts[2]) - 1  # 0-based index
        
        from handlers.movie import send_part
        await send_part(query, context, code, part_index)
    
    # ==================== O'CHIRISH TASDIQLASH ====================
    elif data.startswith("confirm_yes_"):
        # confirm_yes_123 - 123 kodli kinoni o'chirishni tasdiqlash
        code = int(data.replace("confirm_yes_", ""))
        
        from handlers.admin import admin_delete_execute
        await admin_delete_execute(query, context, code)
    
    elif data.startswith("confirm_no_"):
        # confirm_no_123 - 123 kodli kinoni o'chirishni bekor qilish
        code = data.replace("confirm_no_", "")
        
        await query.edit_message_text(
            f"❌ O'chirish bekor qilindi. (Kod: {code})",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
 )
    
    # ==================== YORDAM ====================
    elif data == "show_help":
        await show_help_callback(query)
    
    # ==================== NOMA'LUM TUGMA ====================
    else:
        logger.warning(f"⚠️ Noma'lum callback data: {data}")
        await query.answer("❌ Noma'lum buyruq!", show_alert=True)


async def show_main_menu_callback(query, user_name: str):
    """Callback uchun asosiy menyu"""
    buttons = []
    row = []
    
    for i, (code, cat) in enumerate(CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(
            f"{cat['emoji']} {cat['name']}",
            callback_data=f"cat_{code}"
        ))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    
    if row:
        buttons.append(row)
    
    buttons.append([
        InlineKeyboardButton("📋 KINOLAR RO'YXATI", callback_data="show_movielist"),
        InlineKeyboardButton("🆘 YORDAM", callback_data="show_help")
    ])
    
    await query.edit_message_text(
        f"👋 <b>{user_name}</b>, asosiy menyuga qaytdingiz!\n\n"
        f"Quyidagi kategoriyalardan birini tanlang:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
 )


async def show_movielist_by_category(query, context, category: str):
    """Kategoriya bo'yicha kinolar ro'yxatini ko'rsatish"""
    from database import db
    
    category_name = CATEGORIES[category]["name"]
    category_emoji = CATEGORIES[category]["emoji"]
    
    # Kategoriyadagi kinolarni olish
    movies = db.get_movies_by_category(category)
    
    if not movies:
        await query.edit_message_text(
            f"{category_emoji} <b>{category_name}LAR</b>\n\n"
            f"Bu kategoriyada hali kinolar yo'q.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]]),
            parse_mode="HTML"
 )
        return
    
    # 20 tadan sahifalash
    from utils.helpers import paginate_list
    page = 1
    items_per_page = 20
    
    paginated = paginate_list(movies, page, items_per_page)
    
    text = f"{category_emoji} <b>{category_name}LAR ({len(movies)} ta)</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for movie in paginated['items']:
        parts_count = len(movie.get('parts', [1]))
        parts_text = f" ({parts_count} qism)" if parts_count > 1 else ""
        text += f"🎬 {movie['code']}. {movie['name']}{parts_text}\n"
    
    if paginated['total_pages'] > 1:
        text += f"\n📄 Sahifa {page}/{paginated['total_pages']}"
    
    # Tugmalar
    buttons = []
    
    if paginated['has_next']:
        buttons.append([
            InlineKeyboardButton("⬅️ Oldingi", callback_data=f"catpage_{category}_{page-1}"),
            InlineKeyboardButton("Keyingi ➡️", callback_data=f"catpage_{category}_{page+1}")
        ])
    
    buttons.append([
        InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
 )


async def show_movielist_by_category_page(query, context, category: str, page: int):
    """Kategoriya bo'yicha kinolar ro'yxati - sahifalangan"""
    from database import db
    from utils.helpers import paginate_list
    
    category_name = CATEGORIES[category]["name"]
    category_emoji = CATEGORIES[category]["emoji"]
    
    movies = db.get_movies_by_category(category)
    items_per_page = 20
    
    paginated = paginate_list(movies, page, items_per_page)
    
    text = f"{category_emoji} <b>{category_name}LAR ({len(movies)} ta)</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    for movie in paginated['items']:
        parts_count = len(movie.get('parts', [1]))
        parts_text = f" ({parts_count} qism)" if parts_count > 1 else ""
        text += f"🎬 {movie['code']}. {movie['name']}{parts_text}\n"
    
    text += f"\n📄 Sahifa {page}/{paginated['total_pages']}"
    
    # Tugmalar
    buttons = []
    nav_buttons = []
    
    if paginated['has_previous']:
        nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"catpage_{category}_{page-1}"))
    
    if paginated['has_next']:
        nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"catpage_{category}_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([
        InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
 )


async def show_movielist_page(query, context, page: int):
    """Umumiy kinolar ro'yxati - sahifalangan"""
    from database import db
    from utils.helpers import paginate_list, group_by_category
    
    all_movies = db.get_all_movies()
    items_per_page = 15
    
    paginated = paginate_list(all_movies, page, items_per_page)
    
    text = f"📋 <b>KINOLAR RO'YXATI ({len(all_movies)} ta)</b>\n"
    text += "━━━━━━━━━━━━━━━━━━━━━━\n"
    
    # Kategoriya bo'yicha guruhlash
    grouped = group_by_category(paginated['items'])
    
    for category, movies in grouped.items():
        if category in CATEGORIES:
            emoji = CATEGORIES[category]["emoji"]
            text += f"\n{emoji} <b>{category.upper()}</b>\n"
            
            for movie in movies:
                parts_count = len(movie.get('parts', [1]))
                parts_text = f" ({parts_count} qism)" if parts_count > 1 else ""
                text += f"  ├─ {movie['code']}. {movie['name']}{parts_text}\n"
    
    text += f"\n📄 Sahifa {page}/{paginated['total_pages']}"
    
    # Tugmalar
    buttons = []
    nav_buttons = []
    
    if paginated['has_previous']:
        nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"page_{page-1}"))
    
    if paginated['has_next']:
        nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"page_{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    buttons.append([
        InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
    ])
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
 )


async def show_help_callback(query):
    """Callback uchun yordam xabari"""
    help_text = (
        "🆘 <b>YORDAM</b>\n\n"
        "📌 <b>QANDAY ISHLATILADI?</b>\n"
        "1. Kategoriya tanlang (Kino/Serial/Multfilm)\n"
        "2. Kino kodini kiriting (masalan: 123)\n"
        "3. Kinoni tomosha qiling\n\n"
        
        "📌 <b>KINO KODI QANDAY TOPILADI?</b>\n"
        "• 📋 Kinolar ro'yxati tugmasini bosing\n"
        "• Barcha kinolar kodlari bilan ko'rsatiladi\n\n"
        
        "📌 <b>AGAR SERIAL BO'LSA?</b>\n"
        "• Serial kodini kiriting\n"
        "• Qaysi qism kerakligini tanlang\n\n"
        
        "📌 <b>ADMIN UCHUN:</b>\n"
        "• /addmovie - kino qo'shish\n"
        "• /delete - kino o'chirish\n"
        "• /send - xabar yuborish\n"
        "• /stats - statistika"
    )
    
    buttons = [[InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")]]
    
    await query.edit_message_text(
        help_text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML"
 )
