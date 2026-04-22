from aiogram import types, F, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db
from utils.tokens import TokenManager
from config import MONOBANK_CARD, PRIVAT_CARD, DONATION_BONUSES, DONATELLO_URL, POPPY_URL, ADMIN_ID

# Глобальна змінна для бота (встановлюється в main)
bot = None

def set_bot(bot_instance):
    global bot
    bot = bot_instance

def register_donate_handlers(dp):
    
    @dp.message(F.text == "💰 Підтримати")
    @dp.message(Command("donate"))
    async def show_donate_options(message: types.Message):
        user_id = message.from_user.id
        
        text = "💖 **Підтримати Incognito Love** 💖\n\n"
        text += "Ваша підтримка допомагає розвивати бота!\n\n"
        text += "**🎁 Бонуси за донати:**\n"
        
        for amount, bonus in DONATION_BONUSES.items():
            text += f"• **{amount} грн** → {bonus['tokens']} токенів"
            if bonus['premium_days'] > 0:
                text += f" + {bonus['premium_days']} днів Premium"
            text += "\n"
        
        text += f"\n**💳 Реквізити:**\n"
        text += f"• **Monobank:** `{MONOBANK_CARD}`\n"
        text += f"• **ПриватБанк:** `{PRIVAT_CARD}`\n\n"
        text += f"📌 **В призначенні обов'язково вкажіть:**\n"
        text += f"`{user_id}` (це ваш Telegram ID)\n\n"
        text += "📸 Після переказу надішліть скріншот сюди!\n"
        text += "Бонус нарахують протягом 12 годин."
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Надіслати скріншот", callback_data="send_screenshot")],
            [InlineKeyboardButton(text="🌐 Donatello", url=DONATELLO_URL)],
            [InlineKeyboardButton(text="🌸 Poppy", url=POPPY_URL)],
            [InlineKeyboardButton(text="❓ Як знайти свій ID", callback_data="how_to_find_id")]
        ])
        
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    
    @dp.callback_query(F.data == "send_screenshot")
    async def screenshot_prompt(callback: types.CallbackQuery):
        await callback.message.answer(
            "📸 **Надішліть скріншот переказу**\n\n"
            "На скріншоті має бути видно:\n"
            "• Суму переказу\n"
            "• Ваш Telegram ID в призначенні\n"
            "• Дату переказу\n\n"
            "Після перевірки вам нарахують бонус!"
        )
        await callback.answer()
    
    @dp.callback_query(F.data == "how_to_find_id")
    async def how_to_find_id(callback: types.CallbackQuery):
        await callback.message.answer(
            "🔍 **Як знайти свій Telegram ID:**\n\n"
            "1. Напишіть @userinfobot\n"
            "2. Натисніть /start\n"
            "3. Бот покаже ваш ID\n\n"
            "Або просто напишіть /id в цьому боті"
        )
        await callback.answer()
    
    @dp.message(Command("id"))
    async def show_user_id(message: types.Message):
        await message.answer(f"🆔 Ваш Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")
    
    @dp.message(F.photo)
    async def handle_screenshot(message: types.Message):
        """Обробка скріншотів донатів (тільки для адміна)"""
        user_id = message.from_user.id
        photo_id = message.photo[-1].file_id
        caption = message.caption or ""
        
        # Перевіряємо чи це скріншот донату
        if "скрін" in caption.lower() or "донат" in caption.lower() or "переказ" in caption.lower():
            # Зберігаємо в БД
            with get_db() as conn:
                conn.execute("""
                    INSERT INTO donations (user_id, screenshot_file_id, status, created_at)
                    VALUES (?, ?, 'pending', ?)
                """, (user_id, photo_id, int(time.time())))
            
            # Відправляємо адміну на перевірку
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Підтвердити", callback_data=f"approve_{user_id}"),
                 InlineKeyboardButton(text="❌ Відхилити", callback_data=f"reject_{user_id}")]
            ])
            
            if bot:
                await bot.send_photo(
                    ADMIN_ID,
                    photo_id,
                    caption=f"📸 Новий донат від {user_id}\n{caption}",
                    reply_markup=kb
                )
            
            await message.answer(
                "✅ Скріншот отримано! Адміністратор перевірить і нарахує бонус протягом 12 годин.\n\n"
                "Дякуємо за підтримку! 💖"
            )
    
    @dp.callback_query(F.data.startswith("approve_"))
    async def approve_donation(callback: types.CallbackQuery):
        user_id = int(callback.data.split("_")[1])
        
        # Тут потрібно вказати суму донату (в адмін-панелі)
        await callback.message.answer(f"Введіть суму донату для користувача {user_id}:")
        # Для простоти - нарахуємо стандартний бонус
        TokenManager.add_tokens(user_id, 100, "admin_donation_bonus")
        
        if bot:
            await bot.send_message(user_id, "🎉 Ваш донат підтверджено! Ви отримали 100 токенів бонусом! Дякуємо! 💖")
        
        await callback.message.edit_text("✅ Донат підтверджено, бонус нараховано!")
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("reject_"))
    async def reject_donation(callback: types.CallbackQuery):
        user_id = int(callback.data.split("_")[1])
        
        if bot:
            await bot.send_message(user_id, "❌ Ваш донат не підтверджено. Перевірте правильність скріншоту та повторіть спробу.")
        
        await callback.message.edit_text("❌ Донат відхилено")
        await callback.answer()