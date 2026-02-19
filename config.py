BOT_TOKEN = "BOT_TOKENINGIZNI_BU_YERGA_YOZING"
ADMIN_ID = 123456789   # O'zingizning Telegram user ID (raqam bilan)

DATABASE_URL = "postgresql://user:password@localhost:5432/kinobot"

LOG_LEVEL = "INFO"
DEBUG = False

CATEGORIES = {
    "kino": {
        "name": "Kino",
        "emoji": "🎬"
    },
    "serial": {
        "name": "Serial",
        "emoji": "📺"
    },
    "multfilm": {
        "name": "Multfilm",
        "emoji": "🐰"
    }
}

CALLBACK_PATTERNS = {
    "home_menu": "home_menu",
    "category_": "kategoriya_",
    "confirm_delete": "confirm_delete_",
    "cancel_delete": "cancel_delete"
}
