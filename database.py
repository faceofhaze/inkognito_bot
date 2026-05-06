import sqlite3
import time
from datetime import date
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = sqlite3.connect("inkognito_love.db", timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        # Користувачі
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                   (tg_id INTEGER PRIMARY KEY,
                    name TEXT, age INTEGER, city TEXT, 
                    photo_id TEXT, gender TEXT, 
                    anonymous_name TEXT, 
                    premium_until INTEGER DEFAULT 0,
                    boost_until INTEGER DEFAULT 0,
                    reputation INTEGER DEFAULT 0,
                    is_banned INTEGER DEFAULT 0)''')
        
        # Токени
        conn.execute('''CREATE TABLE IF NOT EXISTS user_tokens 
                   (user_id INTEGER PRIMARY KEY,
                    balance INTEGER DEFAULT 0,
                    total_earned INTEGER DEFAULT 0,
                    last_daily_bonus TEXT)''')
        
        # Лайки
        conn.execute('''CREATE TABLE IF NOT EXISTS likes 
                   (from_id INTEGER, to_id INTEGER, created_at INTEGER,
                    PRIMARY KEY(from_id, to_id))''')
        
        # Активні чати
        conn.execute('''CREATE TABLE IF NOT EXISTS active_chats 
                   (user_one INTEGER, user_two INTEGER,
                    chat_started INTEGER DEFAULT 0,
                    extended_until INTEGER DEFAULT 0)''')
        
        # Подарунки
        conn.execute('''CREATE TABLE IF NOT EXISTS gifts 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_id INTEGER, to_id INTEGER,
                    gift_type TEXT, sent_at INTEGER)''')
        
        # Скарги
        conn.execute('''CREATE TABLE IF NOT EXISTS reports 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER, reported_id INTEGER,
                    reason TEXT, created_at INTEGER)''')
        
        # Денні ліміти
        conn.execute('''CREATE TABLE IF NOT EXISTS daily_limits 
                   (user_id INTEGER, date TEXT,
                    likes_used INTEGER DEFAULT 0,
                    PRIMARY KEY(user_id, date))''')
        
        # Транзакції донатів
        conn.execute('''CREATE TABLE IF NOT EXISTS donations 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER, amount INTEGER,
                    screenshot_file_id TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at INTEGER,
                    processed_at INTEGER)''')
        
        # Реферали (НОВА ТАБЛИЦЯ)
        conn.execute('''CREATE TABLE IF NOT EXISTS referrals 
                   (user_id INTEGER PRIMARY KEY,
                    invited_by INTEGER,
                    invited_at INTEGER)''')
        
        print("✅ База даних готова")