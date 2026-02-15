import logging
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext

logger = logging.getLogger(__name__)


async def callback_handler(update: Update, context: CallbackContext):
    """Barcha callback tugmalarni qayta ishlash"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    logger.info(f"Callback: {data}")
    
    # ==================== OBUNA TEKSHIRISH ====================
    if data == "check_subscription":
        from handlers.start import check_subscription
        is_subscribed, _, channels = await check_subscription(update, context)
        
        if is_subscribed:
            await query.edit_message_text(
                "✅ Obuna tasdiqlandi! /start ni bosing."
            )
        else:
            await query.answer(
                "❌ Hali ham obuna bo'lmagansiz!",
                show_alert=True
            )
    
    # ==================== ASOSIY MENYU ====================
    elif data == "back_to_main":
        from handlers.start import back_to_main
        await back_to_main(update, context)
    
    # ==================== YORDAM ====================
    elif data == "show_help":
        from handlers.start import show_help
        await show_help(update, context)
    
    # ==================== KATEGORIYA TANLASH ====================
    elif data.startswith("cat_"):
        from handlers.movie import category_handler
        await category_handler(update, context)
    
    # ==================== KATEGORIYA RO'YXATI ====================
    elif data.startswith("list_"):
        from handlers.movie import show_category_movielist
        await show_category_movielist(update, context)
    
    # ==================== UMUMIY RO'YXAT ====================
    elif data == "show_movielist":
        from handlers.movie import show_movielist
        await show_movielist(update, context)
    
    # ==================== RO'YXAT SAHIFALARI ====================
    elif data.startswith("page_"):
        from handlers.movie import show_movielist_page
        page = int(data.split("_")[1])
        await show_movielist_page(update, context, page)
    
    # ==================== KATEGORIYA SAHIFALARI ====================
    elif data.startswith("catpage_"):
        from handlers.movie import show_category_page
        parts = data.split("_")
        category = parts[1]
        page = int(parts[2])
        await show_category_page(update, context, category, page)
    
    # ==================== SERIAL QISMLARI ====================
    elif data.startswith("parts_"):
        from handlers.movie import show_parts
        code = int(data.split("_")[1])
        await show_parts(update, context, code)
    
    # ==================== QISM YUBORISH ====================
    elif data.startswith("part_"):
        from handlers.movie import send_part
        parts = data.split("_")
        code = int(parts[1])
        part_index = int(parts[2]) - 1
        await send_part(update, context, code, part_index)
    
    # ==================== O'CHIRISH TASDIQLASH ====================
    elif data.startswith("confirm_yes_"):
        from handlers.admin import admin_delete_execute
        code = int(data.split("_")[2])
        await admin_delete_execute(update, context, code)
    
    elif data.startswith("confirm_no_"):
        code = data.split("_")[2]
        await query.edit_message_text(
            f"❌ O'chirish bekor qilindi (Kod: {code})",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 ASOSIY MENYU", callback_data="back_to_main")
            ]])
        )
    
    # ==================== ADMIN DELETE ====================
    elif data.startswith("delete_cat_"):
        from handlers.admin import delete_movie_category
        await delete_movie_category(update, context)
    
    elif data == "back_to_admin_delete":
        from handlers.admin import back_to_admin_delete
        await back_to_admin_delete(update, context)
    
    # ==================== BROADCAST ====================
    elif data.startswith("broadcast_"):
        from handlers.admin import broadcast_confirm
        await broadcast_confirm(update, context)
    
    # ==================== NOMA'LUM ====================
    else:
        logger.warning(f"Noma'lum callback data: {data}")
        await query.answer("❌ Noma'lum buyruq!", show_alert=True)
