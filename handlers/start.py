from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db
from utils.tokens import TokenManager
from utils.helpers import generate_anonymous_name
from config import ADMIN_ID, BOT_USERNAME
import time

class Registration(StatesGroup):
    name = State()
    age = State()
    city = State()
    photo = State()
    gender = State()

def register_start_handlers(dp):
    
    @dp.message(Command("start"))
    async def start_cmd(message: types.Message, state: FSMContext):
        user_id = message.from_user.id
        
        # Перевірка на реферальне посилання
        args = message.text.split()
        referrer_id = None
        if len(args) > 1 and args[1].startswith("ref_"):
            try:
                referrer_id = int(args[1].split("_")[1])
            except:
                pass
        
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE tg_id=?", (user_id,)).fetchone()
            
            if not user and referrer_id and referrer_id != user_id:
                # Новий користувач прийшов по реферальному посиланню
                existing_ref = conn.execute("SELECT * FROM referrals WHERE user_id=?", (user_id,)).fetchone()
                if not existing_ref:
                    conn.execute("INSERT INTO referrals (user_id, invited_by, invited_at) VALUES (?, ?, ?)",
                                (user_id, referrer_id, int(time.time())))
                    
                    # Бонус тому хто запросив
                    TokenManager.add_tokens(referrer_id, 20, "referral_bonus")
                    try:
                        await message.bot.send_message(referrer_id, "🎉 Ви отримали 20 токенів за запрошення друга!")
                    except:
                        pass
        
        with get_db() as conn:
            user = conn.execute("SELECT * FROM users WHERE tg_id=?", (user_id,)).fetchone()
        
        if user:
            bonus = TokenManager.daily_bonus(user_id)
            bonus_text = f"\n🎁 Отримано {bonus} токенів за вхід!" if bonus > 0 else ""
            balance = TokenManager.get_balance(user_id)
            
            kb = ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="🔍 Пошук"), KeyboardButton(text="💎 VIP")],
                    [KeyboardButton(text="🪙 Токени"), KeyboardButton(text="💰 Підтримати")],
                    [KeyboardButton(text="📊 Профіль"), KeyboardButton(text="🎁 Подарунки")]
                ],
                resize_keyboard=True
            )
            
            await message.answer(
                f"🔞 Вітаю в **Inkognito Love**!{bonus_text}\n\n"
                f"🪙 Баланс: {balance} токенів\n\n"
                f"Оберіть дію:",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "🔞 **Ласкаво просимо до Inkognito Love!** 🔞\n\n"
                "Це анонімний дейтинг бот для дорослих (18+).\n\n"
                "Натисніть кнопку для реєстрації:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="✅ Почати реєстрацію")]],
                    resize_keyboard=True
                )
            )
            await state.set_state(Registration.name)
    
    @dp.message(Command("help"))
    async def help_command(message: types.Message):
        user_id = message.from_user.id
        balance = TokenManager.get_balance(user_id)
        
        text = "🤖 **Inkognito Love - Довідка** 🤖\n\n"
        text += "**📋 Основні команди:**\n"
        text += "• /start - Головне меню\n"
        text += "• /search - Пошук анкет\n"
        text += "• /profile - Мій профіль\n"
        text += "• /donate - Підтримати бота\n"
        text += "• /top - Топ користувачів\n"
        text += "• /referral - Реферальне посилання\n"
        text += "• /help - Ця довідка\n\n"
        
        text += "**🪙 Токени:**\n"
        text += f"• Ваш баланс: {balance} токенів\n"
        text += "• Отримайте токени за донати\n"
        text += "• +20 токенів за запрошення друга\n"
        text += "• Щоденний бонус: 5 токенів\n\n"
        
        text += "**💡 Поради:**\n"
        text += "• Заповніть профіль повністю\n"
        text += "• Додайте гарне фото\n"
        text += "• Будьте ввічливі в чатах\n\n"
        
        text += "**🔒 Безпека:**\n"
        text += "• Всі чати анонімні\n"
        text += "• Ми не зберігаємо історію\n"
        text += "• На скарги реагуємо миттєво\n"
        
        await message.answer(text, parse_mode="Markdown")
    
    @dp.message(Command("referral"))
    async def referral_link(message: types.Message):
        user_id = message.from_user.id
        link = f"https://t.me/{BOT_USERNAME}?start=ref_{user_id}"
        
        # Перевіряємо скільки друзів вже запросив
        with get_db() as conn:
            invited = conn.execute("SELECT COUNT(*) as cnt FROM referrals WHERE invited_by=?", (user_id,)).fetchone()
        
        text = "🔗 **Ваше реферальне посилання:**\n\n"
        text += f"`{link}`\n\n"
        text += "**Як це працює:**\n"
        text += "• Запросіть друга через це посилання\n"
        text += "• Друг отримає +20 токенів при реєстрації\n"
        text += "• Ви отримаєте +20 токенів\n\n"
        text += f"📊 Ви вже запросили: **{invited['cnt']}** друзів\n\n"
        text += "💰 **Бонус:** 20 токенів за кожного друга!"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 Поділитись посиланням", url=f"https://t.me/share/url?url={link}&text=Приєднуйся до Inkognito Love!")]
        ])
        
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    
    @dp.message(Registration.name, F.text == "✅ Почати реєстрацію")
    async def start_registration(message: types.Message, state: FSMContext):
        await state.set_state(Registration.name)
        await message.answer("Як вас звати?", reply_markup=types.ReplyKeyboardRemove())
    
    @dp.message(Registration.name)
    async def process_name(message: types.Message, state: FSMContext):
        if len(message.text) < 2:
            await message.answer("Ім'я занадто коротке")
            return
        await state.update_data(name=message.text)
        kb = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="👨 Чоловік"), KeyboardButton(text="👩 Жінка")]],
            resize_keyboard=True
        )
        await message.answer("Ваша стать:", reply_markup=kb)
        await state.set_state(Registration.gender)
    
    @dp.message(Registration.gender, F.text.in_(["👨 Чоловік", "👩 Жінка"]))
    async def process_gender(message: types.Message, state: FSMContext):
        gender = "male" if message.text == "👨 Чоловік" else "female"
        await state.update_data(gender=gender)
        await message.answer("Скільки вам років?", reply_markup=types.ReplyKeyboardRemove())
        await state.set_state(Registration.age)
    
    @dp.message(Registration.age)
    async def process_age(message: types.Message, state: FSMContext):
        if not message.text.isdigit() or not (18 <= int(message.text) <= 99):
            await message.answer("Введіть вік від 18 до 99")
            return
        await state.update_data(age=int(message.text))
        await message.answer("Ваше місто:")
        await state.set_state(Registration.city)
    
    @dp.message(Registration.city)
    async def process_city(message: types.Message, state: FSMContext):
        if len(message.text) < 2:
            await message.answer("Введіть коректну назву міста")
            return
        await state.update_data(city=message.text)
        await message.answer("📸 Відправте своє фото для анкети")
        await state.set_state(Registration.photo)
    
    @dp.message(Registration.photo, F.photo)
    async def process_photo(message: types.Message, state: FSMContext):
        data = await state.get_data()
        photo_id = message.photo[-1].file_id
        anonymous_name = generate_anonymous_name()
        
        with get_db() as conn:
            conn.execute("""
                INSERT INTO users (tg_id, name, age, city, photo_id, gender, anonymous_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message.from_user.id, data['name'], data['age'], data['city'], photo_id, data['gender'], anonymous_name))
            
            # Перевіряємо чи є реферальний бонус для нового користувача
            ref = conn.execute("SELECT invited_by FROM referrals WHERE user_id=?", (message.from_user.id,)).fetchone()
            if ref:
                TokenManager.add_tokens(message.from_user.id, 20, "referral_joined")
        
        TokenManager.add_tokens(message.from_user.id, 20, "registration_bonus")
        
        kb = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="🔍 Пошук"), KeyboardButton(text="💎 VIP")],
                [KeyboardButton(text="🪙 Токени"), KeyboardButton(text="💰 Підтримати")],
                [KeyboardButton(text="📊 Профіль"), KeyboardButton(text="🎁 Подарунки")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            f"✅ **Реєстрація завершена!**\n\n"
            f"🔒 Ваш нік: `{anonymous_name}`\n"
            f"🎂 Вік: {data['age']}\n"
            f"📍 Місто: {data['city']}\n\n"
            f"🎁 Ви отримали **20 токенів** бонусом!\n\n"
            f"💡 Використайте /referral щоб отримати своє реферальне посилання!",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        await state.clear()