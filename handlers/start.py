from aiogram import types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from database import get_db
from utils.tokens import TokenManager
from utils.helpers import generate_anonymous_name
from config import ADMIN_ID

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
                f"🔞 Вітаю в **Incognito Love**!{bonus_text}\n\n"
                f"🪙 Баланс: {balance} токенів\n\n"
                f"Оберіть дію:",
                reply_markup=kb,
                parse_mode="Markdown"
            )
        else:
            await message.answer(
                "🔞 **Ласкаво просимо до Incognito Love!** 🔞\n\n"
                "Це анонімний дейтинг бот для дорослих (18+).\n\n"
                "Натисніть кнопку для реєстрації:",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="✅ Почати реєстрацію")]],
                    resize_keyboard=True
                )
            )
            await state.set_state(Registration.name)
    
    @dp.message(Registration.name, F.text == "✅ Почати реєстрацію")
    async def start_registration(message: types.Message, state: FSMContext):
        await state.set_state(Registration.name)
        await message.answer("Як вас звати?", reply_markup=types.ReplyKeyboardRemove())
    
    @dp.message(Registration.name)
    async def process_name(message: types.Message, state: FSMContext):
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
            f"🎁 Ви отримали **20 токенів** бонусом!",
            reply_markup=kb,
            parse_mode="Markdown"
        )
        await state.clear()