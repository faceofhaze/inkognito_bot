from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db

def register_block_handlers(dp)
    
    @dp.message(Command(block))
    async def block_user_start(message types.Message)
        text = 🚫 Блокування користувачаnn
        text += Введіть ID користувача, якого хочете заблокувати.n
        text += ID можна знайти в профілі користувача або в чаті.nn
        text += Або натисніть кнопку нижче, щоб побачити свої чати
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=📋 Мої чати, callback_data=my_chats_for_block)]
        ])
        
        await message.answer(text, parse_mode=Markdown, reply_markup=kb)
    
    @dp.callback_query(F.data == my_chats_for_block)
    async def show_chats_for_block(callback types.CallbackQuery)
        user_id = callback.from_user.id
        
        with get_db() as conn
            # Знаходимо активні чати користувача
            chats = conn.execute(
                SELECT user_one, user_two FROM active_chats 
                WHERE user_one= OR user_two=
            , (user_id, user_id)).fetchall()
            
            if not chats
                await callback.message.edit_text(❌ У вас немає активних чатів.)
                return
            
            text = 📋 Ваші активні чатиnn
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            
            for chat in chats
                partner_id = chat['user_two'] if chat['user_one'] == user_id else chat['user_one']
                
                # Отримуємо ім'я партнера
                partner = conn.execute(SELECT anonymous_name FROM users WHERE tg_id=, (partner_id,)).fetchone()
                name = partner['anonymous_name'] if partner else fКористувач {partner_id}
                
                text += f• {name} (ID `{partner_id}`)n
                kb.inline_keyboard.append([
                    InlineKeyboardButton(text=f🚫 Заблокувати {name}, callback_data=fblock_{partner_id})
                ])
            
            text += nАбо введіть ID вручну block ID
            
            await callback.message.edit_text(text, parse_mode=Markdown, reply_markup=kb)
            await callback.answer()
    
    @dp.callback_query(F.data.startswith(block_))
    async def block_callback(callback types.CallbackQuery)
        block_id = int(callback.data.split(_)[1])
        user_id = callback.from_user.id
        
        if block_id == user_id
            await callback.answer(❌ Не можна заблокувати себе!, show_alert=True)
            return
        
        with get_db() as conn
            # Додаємо в чорний список
            conn.execute(INSERT OR IGNORE INTO blacklist (user_id, blocked_id) VALUES (, ), (user_id, block_id))
            
            # Видаляємо активний чат, якщо він є
            conn.execute(
                DELETE FROM active_chats 
                WHERE (user_one= AND user_two=) OR (user_one= AND user_two=)
            , (user_id, block_id, block_id, user_id))
        
        await callback.message.edit_text(f✅ Користувача заблоковано! Ви більше не побачите його анкету.)
        await callback.answer()
    
    @dp.message(Command(unblock))
    async def unblock_menu(message types.Message)
        user_id = message.from_user.id
        
        with get_db() as conn
            blocked = conn.execute(
                SELECT u.tg_id, u.anonymous_name 
                FROM blacklist b
                JOIN users u ON b.blocked_id = u.tg_id
                WHERE b.user_id = 
            , (user_id,)).fetchall()
        
        if not blocked
            await message.answer(❌ У вас немає заблокованих користувачів.)
            return
        
        text = 🔓 Розблокування користувачівnn
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        
        for user in blocked
            text += f• {user['anonymous_name']} (ID `{user['tg_id']}`)n
            kb.inline_keyboard.append([
                InlineKeyboardButton(text=f🔓 Розблокувати {user['anonymous_name']}, callback_data=funblock_{user['tg_id']})
            ])
        
        await message.answer(text, parse_mode=Markdown, reply_markup=kb)
    
    @dp.callback_query(F.data.startswith(unblock_))
    async def unblock_callback(callback types.CallbackQuery)
        unblock_id = int(callback.data.split(_)[1])
        user_id = callback.from_user.id
        
        with get_db() as conn
            conn.execute(DELETE FROM blacklist WHERE user_id= AND blocked_id=, (user_id, unblock_id))
        
        await callback.message.edit_text(f✅ Користувача розблоковано!)
        await callback.answer()
    
    @dp.message(Command(blacklist))
    async def show_blacklist(message types.Message)
        user_id = message.from_user.id
        
        with get_db() as conn
            blocked = conn.execute(
                SELECT u.tg_id, u.anonymous_name 
                FROM blacklist b
                JOIN users u ON b.blocked_id = u.tg_id
                WHERE b.user_id = 
            , (user_id,)).fetchall()
        
        if not blocked
            await message.answer(📋 Ваш чорний список порожній.)
            return
        
        text = 🚫 Ваш чорний списокnn
        for user in blocked
            text += f• {user['anonymous_name']} (ID `{user['tg_id']}`)n
        
        text += nЩоб розблокувати - використайте unblock
        
        await message.answer(text, parse_mode=Markdown)