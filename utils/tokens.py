from database import get_db
from datetime import date

class TokenManager:
    @staticmethod
    def get_balance(user_id):
        with get_db() as conn:
            balance = conn.execute("SELECT balance FROM user_tokens WHERE user_id=?", (user_id,)).fetchone()
            return balance['balance'] if balance else 0
    
    @staticmethod
    def add_tokens(user_id, amount, source):
        with get_db() as conn:
            conn.execute("""
                INSERT INTO user_tokens (user_id, balance, total_earned)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) 
                DO UPDATE SET balance = balance + ?, total_earned = total_earned + ?
            """, (user_id, amount, amount, amount, amount))
            print(f"✅ +{amount} токенів для {user_id} ({source})")
        return True
    
    @staticmethod
    def spend_tokens(user_id, amount, action):
        balance = TokenManager.get_balance(user_id)
        if balance < amount:
            return False
        with get_db() as conn:
            conn.execute("UPDATE user_tokens SET balance = balance - ? WHERE user_id=?", (amount, user_id))
        return True
    
    @staticmethod
    def daily_bonus(user_id):
        today = date.today().isoformat()
        with get_db() as conn:
            last_bonus = conn.execute("SELECT last_daily_bonus FROM user_tokens WHERE user_id=?", (user_id,)).fetchone()
            if last_bonus and last_bonus[0] == today:
                return 0
            bonus = 5
            conn.execute("""
                INSERT INTO user_tokens (user_id, balance, last_daily_bonus)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) 
                DO UPDATE SET balance = balance + ?, last_daily_bonus = ?
            """, (user_id, bonus, today, bonus, today))
            return bonus