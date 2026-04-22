#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import time
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand

# Імпорт конфігурації
import config

# Імпорт бази даних
from database import init_db

# Імпорт хендлерів
from handlers import (
    register_start_handlers,
    register_search_handlers,
    register_chat_handlers,
    register_profile_handlers,
    register_donate_handlers,
    set_bot
)

# ============================================
# НАЛАШТУВАННЯ БОТА
# ============================================
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Передаємо бота в donate handlers
set_bot(bot)

# ============================================
# РЕЄСТРАЦІЯ ВСІХ ХЕНДЛЕРІВ
# ============================================
register_start_handlers(dp)
register_search_handlers(dp)
register_chat_handlers(dp)
register_profile_handlers(dp)
register_donate_handlers(dp)

# ============================================
# КОМАНДИ ДЛЯ МЕНЮ
# ============================================
async def set_commands():
    commands = [
        BotCommand(command="start", description="🏠 Головне меню"),
        BotCommand(command="search", description="🔍 Пошук анкет"),
        BotCommand(command="donate", description="💰 Підтримати бота"),
        BotCommand(command="profile", description="📊 Мій профіль"),
        BotCommand(command="id", description="🆔 Показати мій ID"),
    ]
    await bot.set_my_commands(commands)

# ============================================
# ФОНОВІ ЗАВДАННЯ
# ============================================
async def daily_reset():
    """Скидання щоденних лімітів о півночі"""
    while True:
        now = datetime.now()
        midnight = datetime(now.year, now.month, now.day) + timedelta(days=1)
        wait_seconds = (midnight - now).seconds
        await asyncio.sleep(wait_seconds)
        
        from database import get_db
        with get_db() as conn:
            conn.execute("DELETE FROM daily_limits WHERE date < date('now')")
        
        print("🔄 Щоденні ліміти скинуто")

async def cleanup_inactive():
    """Очищення старих чатів"""
    while True:
        await asyncio.sleep(3600)
        from database import get_db
        with get_db() as conn:
            conn.execute("DELETE FROM active_chats WHERE chat_started < ?", (int(time.time()) - 86400,))
        print("🧹 Очищення чатів виконано")

# ============================================
# ЗАПУСК
# ============================================
async def main():
    # Ініціалізація бази даних
    init_db()
    
    # Встановлення команд
    await set_commands()
    
    # Запуск фонових завдань
    asyncio.create_task(daily_reset())
    asyncio.create_task(cleanup_inactive())
    
    print("=" * 50)
    print("🤖 Incognito Love - Анонімний дейтинг бот")
    print("=" * 50)
    print("✅ Бот запущений!")
    print(f"💰 Картка Monobank: {config.MONOBANK_CARD}")
    print(f"💰 Картка Приват: {config.PRIVAT_CARD}")
    print("=" * 50)
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())