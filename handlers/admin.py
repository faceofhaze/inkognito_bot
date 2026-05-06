from aiogram import types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_db
from config import ADMIN_ID
import time

def register_admin_handlers(dp):
    
    def is_admin(user_id):
        return user_id == ADMIN_ID
    
    @dp.message(Command("admin"))
    async def admin_panel(message: types.Message):
        if not is_admin(message.from_user.id):
            await message.answer("❌ У вас немає доступу до адмін-панелі.")
            return
        
        # Отримуємо статистику
        with get_db() as conn:
            total_users = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()['cnt']
            total_likes = conn.execute("SELECT COUNT(*) as cnt FROM likes").fetchone()['cnt']
            total_gifts = conn.execute("SELECT COUNT(*) as cnt FROM gifts").fetchone()['cnt']
            total_donations = conn.execute("SELECT COUNT(*) as cnt FROM donations WHERE status='pending'").fetchone()['cnt']
            total_reports = conn.execute("SELECT COUNT(*) as cnt FROM reports").fetchone()['cnt']
            premium_users = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE premium_until > ?", (int(time.time()),)).fetchone()['cnt']
        
        text = "👑 **Адмін-панель Inkognito Love** 👑\n\n"
        text += "📊 **Статистика:**\n"
        text += f"• 👥 Користувачів: {total_users}\n"
        text += f"• 👑 Premium: {premium_users}\n"
        text += f"• ❤️ Лайків: {total_likes}\n"
        text += f"• 🎁 Подарунків: {total_gifts}\n"
        text += f"• ⏳ Очікують донатів: {total_donations}\n"
        text += f"• ⚠️ Скарг: {total_reports}\n\n"
        text += "**Оберіть дію:**"
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📢 Розсилка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="⚠️ Скарги", callback_data="admin_reports")],
            [InlineKeyboardButton(text="💰 Донати", callback_data="admin_donations")],
            [InlineKeyboardButton(text="📊 Детальна статистика", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🚫 Бан користувача", callback_data="admin_ban")],
            [InlineKeyboardButton(text="🔓 Розбан", callback_data="admin_unban")]
        ])
        
        await message.answer(text, parse_mode="Markdown", reply_markup=kb)
    
    @dp.callback_query(F.data == "admin_broadcast")
    async def admin_broadcast_prompt(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Немає доступу")
            return
        
        await callback.message.answer("📢 Введіть текст для розсилки всім користувачам:")
        await callback.answer()
    
    @dp.message(lambda msg: msg.from_user.id == ADMIN_ID and msg.text and not msg.text.startswith('/'))
    async def send_broadcast(message: types.Message):
        text = message.text
        
        with get_db() as conn:
            users = conn.execute("SELECT tg_id FROM users").fetchall()
        
        sent = 0
        failed = 0
        
        await message.answer(f"📢 Починаю розсилку для {len(users)} користувачів...")
        
        for user in users:
            try:
                await message.bot.send_message(user['tg_id'], f"📢 **Оголошення від адміна:**\n\n{text}", parse_mode="Markdown")
                sent += 1
            except:
                failed += 1
            await asyncio.sleep(0.05)  # Щоб не заблокували
        
        await message.answer(f"✅ Розсилка завершена!\n📨 Відправлено: {sent}\n❌ Помилок: {failed}")
    
    @dp.callback_query(F.data == "admin_reports")
    async def admin_view_reports(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Немає доступу")
            return
        
        with get_db() as conn:
            reports = conn.execute("""
                SELECT r.id, r.reporter_id, r.reported_id, r.reason, r.created_at,
                    u1.anonymous_name as reporter_name,
                    u2.anonymous_name as reported_name
                FROM reports r
                JOIN users u1 ON r.reporter_id = u1.tg_id
                JOIN users u2 ON r.reported_id = u2.tg_id
                ORDER BY r.created_at DESC
                LIMIT 20
            """).fetchall()
        
        if not reports:
            await callback.message.edit_text("⚠️ Немає скарг.")
            return
        
        text = "⚠️ **Останні скарги:**\n\n"
        kb = InlineKeyboardMarkup(inline_keyboard=[])
        
        for r in reports:
            text += f"📌 Скарга #{r['id']}\n"
            text += f"• Від: {r['reporter_name']}\n"
            text += f"• На: {r['reported_name']}\n"
            text += f"• Причина: {r['reason']}\n"
            text += f"• Час: {time.ctime(r['created_at'])}\n\n"
            kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"🚫 Забанити {r['reported_name']}", callback_data=f"admin_ban_user_{r['reported_id']}")
            ])
        
        await callback.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
        await callback.answer()
    
    @dp.callback_query(F.data.startswith("admin_ban_user_"))
    async def admin_ban_user(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Немає доступу")
            return
        
        user_id = int(callback.data.split("_")[3])
        
        with get_db() as conn:
            conn.execute("UPDATE users SET is_banned=1 WHERE tg_id=?", (user_id,))
        
        await callback.message.edit_text(f"✅ Користувача {user_id} забанено!")
        await callback.answer()
    
    @dp.callback_query(F.data == "admin_stats")
    async def admin_detailed_stats(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Немає доступу")
            return
        
        with get_db() as conn:
            # Статистика по днях
            today = time.strftime("%Y-%m-%d")
            today_likes = conn.execute("SELECT COUNT(*) as cnt FROM likes WHERE date(created_at, 'unixepoch') = date('now')").fetchone()['cnt']
            today_users = conn.execute("SELECT COUNT(*) as cnt FROM users WHERE date(premium_until, 'unixepoch', 'unixepoch') = date('now')").fetchone()['cnt']
            
            total_tokens = conn.execute("SELECT SUM(balance) as total FROM user_tokens").fetchone()['total'] or 0
        
        text = "📊 **Детальна статистика:**\n\n"
        text += f"📅 За сьогодні:\n"
        text += f"• ❤️ Лайків: {today_likes}\n"
        text += f"• 👑 Нових Premium: {today_users}\n\n"
        text += f"💰 Всього токенів у системі: {total_tokens}\n"
        
        await callback.message.edit_text(text, parse_mode="Markdown")
        await callback.answer()
    
    @dp.callback_query(F.data == "admin_donations")
    async def admin_donations(callback: types.CallbackQuery):
        if not is_admin(callback.from_user.id):
            await callback.answer("❌ Немає доступу")
            return
        
        with get_db() as conn:
            donations = conn.execute("""
                SELECT id, user_id, amount, screenshot_file_id, status, created_at
                FROM donations
                WHERE status = 'pending'
                ORDER BY created_at DESC
            """).fetchall()
        
        if not donations:
            await callback.message.edit_text("💰 Немає очікуючих донатів.")
            return
        
        text = "💰 **Очікуючі донати:**\n\n"
        
        for d in donations:
            text += f"📌 Донат #{d['id']}\n"
            text += f"• Користувач: {d['user_id']}\n"
            text += f"• Сума: {d['amount']} грн\n"
            text += f"• Час: {time.ctime(d['created_at'])}\n\n"
        
        await callback.message.edit_text(text, parse_mode="Markdown")
        await callback.answer()