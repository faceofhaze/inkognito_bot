import random
from database import get_db
from datetime import date

def is_premium(user_id):
    with get_db() as conn:
        user = conn.execute("SELECT premium_until FROM users WHERE tg_id=?", (user_id,)).fetchone()
        return user and user['premium_until'] > int(time.time())

def can_like(user_id):
    today = date.today().isoformat()
    with get_db() as conn:
        limit = conn.execute(
            "SELECT likes_used FROM daily_limits WHERE user_id=? AND date=?",
            (user_id, today)
        ).fetchone()
        used = limit['likes_used'] if limit else 0
        from config import FREE_DAILY_LIKES
        return used < FREE_DAILY_LIKES

def increment_like(user_id):
    today = date.today().isoformat()
    with get_db() as conn:
        conn.execute("""
            INSERT INTO daily_limits (user_id, date, likes_used)
            VALUES (?, ?, 1)
            ON CONFLICT(user_id, date) 
            DO UPDATE SET likes_used = likes_used + 1
        """, (user_id, today))

def generate_anonymous_name():
    prefixes = ["Incognito", "Secret", "Mysterious", "Hidden", "Quiet"]
    return f"{random.choice(prefixes)}_{random.randint(1000, 9999)}"