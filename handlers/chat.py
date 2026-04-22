from aiogram import types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db
from utils.tokens import TokenManager
from config import EXTEND_CHAT_PRICE

def get_chat_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Завершити чат", callback_data="stop_chat")],
        [InlineKeyboardButton(text="🎁 Подарунок", callback_data="gift_menu"),
         InlineKeyboardButton(text=f"⏰ Продовжити ({EXTEND_CHAT_PRICE}🪙)", callback_data="extend_chat")]
    ])

def register_chat_handlers(dp):
    
    @dp.message(F.text & ~F.text.startswith("/") & ~F.text.startswith("🔍") & ~F.text.startswith("💎") & ~F.text.startswith("🪙") & ~F.text.startswith("💰") & ~F.text.startswith("📊") & ~F.text.startswith("🎁"))
    async def chat_proxy(message: types.Message):
        user_id = message.from_user.id
        
        with get_db() as conn:
            chat = conn.execute(
                "SELECT user_one, user_two, extended_until FROM active_chats WHERE user_one=? OR user_two=?",
                (user_id, user_id)
            ).fetchone()
            
            if chat:
                if chat['extended_until'] > 0 and chat['extended_until'] < int(time.time()):
                    await message.answer("⏰ Час чату закінчився. Використайте /search для нового пошуку")
                    conn.execute("DELETE FROM active_chats WHERE user_one=? OR user_two=?", (user_id, user_id))
                    return
                
                recipient_id = chat['user_two'] if chat['user_one'] == user_id else chat['user_one']
                try:
                    await message.bot.send_message(recipient_id, f"💬 {message.text}")
                except:
                    await message.answer("❌ Співрозмовник покинув чат")
                    conn.execute("DELETE FROM active_chats WHERE user_one=? OR user_two=?", (user_id, user_id))
            else:
                await message.answer("❌ Ви не в чаті. Використовуйте /search")
    
    @dp.callback_query(F.data == "stop_chat")
    async def stop_chat(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        
        with get_db() as conn:
            chat = conn.execute("SELECT user_one, user_two FROM active_chats WHERE user_one=? OR user_two=?", 
                               (user_id, user_id)).fetchone()
            if chat:
                partner_id = chat['user_two'] if chat['user_one'] == user_id else chat['user_one']
                conn.execute("DELETE FROM active_chats WHERE user_one=? OR user_two=?", (user_id, user_id))
                await callback.message.edit_text("❌ Чат завершено")
                await callback.bot.send_message(partner_id, "❌ Співрозмовник завершив чат")
        
        await callback.answer()
    
    @dp.callback_query(F.data == "extend_chat")
    async def extend_chat(callback: types.CallbackQuery):
        user_id = callback.from_user.id
        
        if TokenManager.spend_tokens(user_id, EXTEND_CHAT_PRICE, "extend_chat"):
            with get_db() as conn:
                conn.execute("""
                    UPDATE active_chats 
                    SET extended_until = ? 
                    WHERE user_one=? OR user_two=?
                """, (int(time.time()) + 1800, user_id, user_id))
            
            await callback.message.edit_text("⏰ Чат продовжено на 30 хвилин!")
            await callback.answer(f"✅ Чат продовжено! Витрачено {EXTEND_CHAT_PRICE} токенів")
        else:
            await callback.answer("❌ Недостатньо токенів! Натисніть «💰 Підтримати»", show_alert=True)