import os
from dotenv import load_dotenv

# .env faylni yuklash
load_dotenv()

# ================= TELEGRAM =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", "5583787103"))

# ================= DATABASE =================
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/kinobot")

# ================ KANALLAR =================
# Foydalanuvchi botdan foydalanish uchun obuna bo'lishi kerak bo'lgan kanallar
MANDATORY_CHANNELS = os.getenv("MANDATORY_CHANNELS", "k1no_kodlar,foydalanuvchi_id").split(",")

# ================== APP =====================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "False") == "True"

# ================== KATEGORIYALAR ==================
CATEGORIES = {
    "kino": {"name": "Kino", "emoji": "🎬"},
    "serial": {"name": "Serial", "emoji": "📺"},
    "multfilm": {"name": "Multfilm", "emoji": "🐰"}
}

# ================== CALLBACK PATTERNS ==================
CALLBACK_PATTERNS = {
    "home_menu": "home_menu",
    "category_": "kategoriya_",
    "obuna_check": "obuna_tekshir",
    "confirm_delete": "confirm_delete_",
    "cancel_delete": "cancel_delete",
}
