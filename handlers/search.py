from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db
from utils.tokens import TokenManager
from utils.helpers import can_like, increment_like
from config import SUPER_LIKE_PRICE

def register_search_handlers(dp):
    
    @dp.message(F.text == "🔍 Пошук")
    async def search_profiles(message: types.Message):
        user_id = message.from_user.id
        
        if not can_like(user_id):
            await message.answer("❌ Ви використали всі лайки на сьогодні! Завтра буде нові.")
            return
        
        with get_db() as conn:
            user = conn.execute("SELECT gender FROM users WHERE tg_id=?", (user_id,)).fetchone()
            if not user:
                await message.answer("Спочатку зареєструйтесь /start")
                return
            
            target_gender = "female" if user['gender'] == "male" else "male"
            
            profile = conn.execute("""
                SELECT tg_id, age, city, photo_id, anonymous_name
                FROM users 
                WHERE tg_id != ? AND gender = ? AND is_banned = 0
                AND tg_id NOT IN (SELECT to_id FROM likes WHERE from_id = ?)
                ORDER BY RANDOM() LIMIT 1
            """, (user_id, target_gender, user_id)).fetchone()
        
        if profile:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="❤️ Лайк", callback_data=f"like_{profile['tg_id']}"),
                 InlineKeyboardButton(text="👎 Пропустити", callback_data="skip")],
                [InlineKeyboardButton(text=f"⭐ Супер-лайк ({SUPER_LIKE_PRICE}🪙)", callback_data=f"super_{profile['tg_id']}")]
            ])
            
            caption = f"🔥 {profile['anonymous_name']}, {profile['age']} років\n📍 {profile['city']}"
            
            if profile['photo_id']:
                await message.answer_photo(profile['photo_id'], caption=caption, reply_markup=kb)
            else:
                await message.answer(caption, reply_markup=kb)
        else:
            await message.answer("😔 Нових анкет поки немає. Зайдіть пізніше!")
    
    @dp.callback_query(F.data.startswith("like_"))
    async def handle_like(callback: types.CallbackQuery):
        to_id = int(callback.data.split("_")[1])
        from_id = callback.from_user.id
        
        if not can_like(from_id):
            await callback.answer("❌ Ви використали всі лайки!", show_alert=True)
            return
        
        increment_like(from_id)
        
        with get_db() as conn:
            match = conn.execute("SELECT * FROM likes WHERE from_id=? AND to_id=?", (to_id, from_id)).fetchone()
            conn.execute("INSERT OR IGNORE INTO likes VALUES (?, ?, ?)", (from_id, to_id, int(time.time())))
            
            if match:
                conn.execute("INSERT INTO active_chats (user_one, user_two, chat_started) VALUES (?, ?, ?)",
                            (from_id, to_id, int(time.time())))
                
                from handlers.chat import get_chat_keyboard
                
                await callback.bot.send_message(from_id, "🔥 **ВЗАЄМНО!** Чат створено!", reply_markup=get_chat_keyboard())
                await callback.bot.send_message(to_id, "🔥 **ВЗАЄМНО!** Чат створено!", reply_markup=get_chat_keyboard())
                await callback.answer("🎉 Взаємно!", show_alert=True)
            else:
                await callback.answer("❤️ Лайк відправлено!")
    
    @dp.callback_query(F.data == "skip")
    async def skip_profile(callback: types.CallbackQuery):
        await callback.answer("👎 Пропущено")
        await search_profiles(callback.message)
    
    @dp.callback_query(F.data.startswith("super_"))
    async def super_like_handler(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        to_id = int(callback.data.split("_")[1])
        
        if TokenManager.spend_tokens(user_id, SUPER_LIKE_PRICE, "super_like"):
            with get_db() as conn:
                conn.execute("INSERT OR IGNORE INTO likes VALUES (?, ?, ?)", (user_id, to_id, int(time.time())))
            
            await callback.bot.send_message(to_id, "⭐ **ХТОСЬ ВІДПРАВИВ СУПЕР-ЛАЙК!** ⭐")
            await callback.answer(f"✨ Супер-лайк відправлено! Витрачено {SUPER_LIKE_PRICE} токенів", show_alert=True)
        else:
            await callback.answer("❌ Недостатньо токенів! Натисніть «💰 Підтримати»", show_alert=True)