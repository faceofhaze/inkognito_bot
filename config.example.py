# ============================================
# ПРИКЛАД КОНФІГУРАЦІЇ ДЛЯ БОТА
# ============================================
# ІНСТРУКЦІЯ:
# 1. Скопіюй цей файл як "config.py"
# 2. Заповни своїми даними (токен, картки, ID)
# 3. Збережи файл
# ============================================

# ---------- ТОКЕН БОТА ----------
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"

# ---------- НОМЕРИ КАРТОК ----------
MONOBANK_CARD = "4441 1111 1111 1111"
PRIVAT_CARD = "5168 1111 1111 1111"

# ---------- ПОСИЛАННЯ НА ДОНАТИ ----------
DONATELLO_URL = "https://www.donationalerts.com/r/your_username"

# ---------- ID АДМІНА ----------
ADMIN_ID = 123456789

# ---------- БОНУСИ ЗА ДОНАТИ ----------
DONATION_BONUSES = {
    50: {"tokens": 30, "premium_days": 0},
    100: {"tokens": 80, "premium_days": 3},
    200: {"tokens": 200, "premium_days": 7},
    500: {"tokens": 600, "premium_days": 30},
    1000: {"tokens": 1500, "premium_days": 90}
}

# ---------- TELEGRAM STARS ----------
STARS_ENABLED = False

STARS_PACKS = {
    25: {"tokens": 30, "stars": 25},
    50: {"tokens": 65, "stars": 50},
    100: {"tokens": 140, "stars": 100},
    250: {"tokens": 375, "stars": 250},
    500: {"tokens": 800, "stars": 500}
}

# ---------- ЦІНИ В ТОКЕНАХ ----------
SUPER_LIKE_PRICE = 10
BOOST_PRICE = 50
EXTEND_CHAT_PRICE = 25

# ---------- ПОДАРУНКИ ----------
GIFTS = {
    "🌹": {"name": "Троянда", "price": 15},
    "🍫": {"name": "Цукерки", "price": 20},
    "💍": {"name": "Кільце", "price": 50},
    "🧸": {"name": "Ведмедик", "price": 35},
    "🎂": {"name": "Торт", "price": 25}
}

# ---------- ЛІМІТИ ----------
FREE_DAILY_LIKES = 20
FREE_DAILY_CHATS = 5