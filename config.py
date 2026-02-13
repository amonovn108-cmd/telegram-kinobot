import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()


def get_env_int(key: str, default: int) -> int:
    """Xavfsiz int olish"""
    try:
        return int(os.getenv(key, str(default)))
    except (ValueError, TypeError):
        return default


def get_env_list(key: str, default: str = "") -> list:
    """List ni tozalab olish"""
    value = os.getenv(key, default)
    return [v.strip() for v in value.split(",") if v.strip()]


# ==================== TELEGRAM ====================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = get_env_int("ADMIN_ID", 5583787103)

# ==================== DATABASE ====================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/kinobot")

# ================ KANALLAR ====================
# Foydalanuvchi botdan foydalanish uchun obuna bo'lishi kerak bo'lgan kanallar
MANDATORY_CHANNELS = get_env_list("MANDATORY_CHANNELS", "k1no_kodlar,foydalanuvchi_id")

# ================== APP =====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ================== KATEGORIYALAR ====================
CATEGORIES = {
    "kino": {"name": "Kino", "emoji": "🎬"},
    "serial": {"name": "Serial", "emoji": "📺"},
    "multfilm": {"name": "Multfilm", "emoji": "🐰"}
}

# ================== CALLBACK PATTERNS ====================
CALLBACK_PATTERNS = {
    "home_menu": "home_menu",
    "category_": "kategoriya_",
    "obuna_check": "obuna_tekshir",
    "confirm_delete": "confirm_delete_",
    "cancel_delete": "cancel_delete",
}
