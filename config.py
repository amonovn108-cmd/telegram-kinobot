import os

# =========================
# TELEGRAM SOZLAMALAR
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN topilmadi!")

if not ADMIN_ID:
    raise ValueError("❌ ADMIN_ID topilmadi!")

# =========================
# DATABASE SOZLAMALAR
# =========================
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL topilmadi!")

# Railway ba'zida postgres:// beradi
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# =========================
# LOG
# =========================
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# =========================
# KATEGORIYALAR
# =========================
CATEGORIES = {
    "kino": {"name": "Kino", "emoji": "🎬"},
    "serial": {"name": "Serial", "emoji": "📺"},
    "multfilm": {"name": "Multfilm", "emoji": "🐰"}
}

CALLBACK_PATTERNS = {
    "home_menu": "home_menu",
    "category_": "kategoriya_",
    "confirm_delete": "confirm_delete_",
    "cancel_delete": "cancel_delete"
}
