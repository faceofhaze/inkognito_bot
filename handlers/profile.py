from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db
from utils.tokens import TokenManager
from config import TOKEN_PRICES, GIFTS

def register_profile_handlers(dp):
    
    @dp.message(F.text == "📊 Профіль")
    @dp.message(Command("profile"))
    async def show_profile(message: types.Message):
        user_id = message.from_user.id
        balance = TokenManager.get_balance(user_id)
        
        with get_db() as conn:
            user = conn.execute("SELECT name, age, city, anonymous_name, premium_until FROM users WHERE tg_id=?", (user_id,)).fetchone()
            likes_received = conn.execute("SELECT COUNT(*) as cnt FROM likes WHERE to_id=?", (user_id,)).fetchone()
            
            if not user:
                await message.answer("Ви не зареєстровані")
                return
            
            is_premium = user['premium_until'] > int(time.time())
            premium_text = "✅ Активний" if is_premium else "❌ Неактивний"
            
            text = f"📊 **Ваш профіль**\n\n"
            text += f"👤 Ім'я: {user['name']}\n"
            text += f"🔒 Нік: `{user['anonymous_name']}`\n"
            text += f"🎂 Вік: {user['age']}\n"
            text += f"📍 Місто: {user['city']}\n"
            text += f"❤️ Отримано лайків: {likes_received['cnt']}\n"
            text += f"🪙 Токенів: {balance}\n"
            text += f"💎 Premium: {premium_text}\n"
            
            await message.answer(text, parse_mode="Markdown")
    
    @dp.message(F.text == "🪙 Токени")
    async def show_tokens_shop(message: types.Message):
        balance = TokenManager.get_balance(message.from_user.id)
        
        text = f"🪙 **Токени Incognito Love**\n\n"
        text += f"💰 Ваш баланс: **{balance}** токенів\n\n"
        text += "**Що можна купити за токени:**\n"
        text += f"• ⭐ Супер-лайк - {config.SUPER_LIKE_PRICE} токенів\n"
        text += f"• 🚀 Підняти анкету - {config.BOOST_PRICE} токенів\n"
        text += f"• ⏰ Продовжити чат - {config.EXTEND_CHAT_PRICE} токенів\n\n"
        
        text += "**🎁 Подарунки:**\n"
        for emoji, gift in GIFTS.items():
            text += f"• {emoji} {gift['name']} - {gift['price']} токенів\n"
        
        text += "\n💰 Поповнити баланс можна через кнопку «Підтримати»"
        
        await message.answer(text, parse_mode="Markdown")
    
    @dp.message(F.text == "🎁 Подарунки")
    async def gifts_menu(message: types.Message):
        text = "🎁 **Оберіть подарунок для співрозмовника:**\n\n"
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        
        for emoji, gift in GIFTS.items():
            text += f"{emoji} {gift['name']} - {gift['price']} токенів\n"
            kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"{emoji} {gift['name']} ({gift['price']}🪙)", 
                                   callback_data=f"gift_{emoji}")
            ])
        
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    
    @dp.callback_query(F.data.startswith("gift_"))
    async def send_gift(callback: types.CallbackQuery):
        gift_emoji = callback.data.split("_")[1]
        price = GIFTS.get(gift_emoji, {}).get("price", 15)
        
        user_id = callback.from_user.id
        
        with get_db() as conn:
            chat = conn.execute(
                "SELECT user_one, user_two FROM active_chats WHERE user_one=? OR user_two=?",
                (user_id, user_id)
            ).fetchone()
        
        if not chat:
            await callback.answer("❌ Ви не в чаті!", show_alert=True)
            return
        
        partner_id = chat['user_two'] if chat['user_one'] == user_id else chat['user_one']
        
        if TokenManager.spend_tokens(user_id, price, f"gift_{gift_emoji}"):
            with get_db() as conn:
                conn.execute("INSERT INTO gifts (from_id, to_id, gift_type, sent_at) VALUES (?, ?, ?, ?)",
                            (user_id, partner_id, gift_emoji, int(time.time())))
            
            await callback.bot.send_message(partner_id, f"🎁 **Вам відправили подарунок!**\n\n{gift_emoji} Хтось подумав про вас!")
            await callback.message.edit_text(f"✅ Подарунок {gift_emoji} відправлено!")
            await callback.answer()
        else:
            await callback.answer("❌ Недостатньо токенів! Натисніть «💰 Підтримати»", show_alert=True)
    
    @dp.message(F.text == "💎 VIP")
    async def vip_info(message: types.Message):
        text = "💎 **Premium підписка** 💎\n\n"
        text += "**Переваги Premium:**\n"
        text += "• 🚀 Пріоритетний пошук\n"
        text += "• 💎 VIP статус\n"
        text += "• 🎁 5 подарунків/місяць\n"
        text += "• 🔒 Прихований онлайн-статус\n\n"
        text += "💰 **Ціна:** 149 грн/місяць\n\n"
        text += "⭐ Premium можна отримати за донат від 100 грн!\n"
        text += "Натисніть «💰 Підтримати» для деталей"
        
        await message.answer(text, parse_mode="Markdown")