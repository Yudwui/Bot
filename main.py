import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# Токен вашего бота
TOKEN = "8844284513:AAHB1BBs_nE8Zfu72EPomPa28EJtknKcoZI"

# ID администратора (замените на ваш Telegram user_id, чтобы тестировать команду /users)
ADMIN_ID = 8265983880  # Укажите сюда свой ID, если знаете, или оставьте число для примера

dp = Dispatcher()

# --- РАБОТА С БАЗОЙ ДАННЫХ SQLite ---
def init_db():
    """Создаёт таблицу пользователей, если её ещё нет"""
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            registered_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def register_user(user: types.User):
    """Сохраняет пользователя в базу данных при первом обращении"""
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    
    # Проверяем, есть ли пользователь в базе
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user.id,))
    existing_user = cursor.fetchone()
    
    if not existing_user:
        reg_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, registered_at) VALUES (?, ?, ?, ?)",
            (user.id, user.username or "отсутствует", user.first_name, reg_date)
        )
        conn.commit()
    conn.close()

# --- ОБРАБОТЧИКИ КОМАНД ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Регистрируем пользователя в базе при старте
    register_user(message.from_user)
    
    await message.answer(
        f"Привет, {message.from_user.first_name}!\n"
        "Я бот с подключенной базой данных SQLite 🗄️\n\n"
        "Доступные команды:\n"
        "📊 `/stats` — общая статистика пользователей\n"
        "👤 `/profile` — ваш профиль\n"
        "👑 `/users` — список всех пользователей (только для админа)"
    )

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    register_user(message.from_user)
    
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    
    await message.answer(f"📊 **Статистика бота:**\nВсего зарегистрированных пользователей: `{count}`")

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    register_user(message.from_user)
    
    user_id = message.from_user.id
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT username, first_name, registered_at FROM users WHERE user_id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        username, first_name, reg_date = user_data
        await message.answer(
            f"👤 **Ваш профиль:**\n\n"
            f"🆔 ID: `{user_id}`\n"
            f"📛 Имя: {first_name}\n"
            f"🔗 Username: @{username}\n"
            f"📅 Дата регистрации: {reg_date}"
        )
    else:
        await message.answer("❌ Информация о вас не найдена в базе данных.")

@dp.message(Command("users"))
async def cmd_users(message: types.Message):
    register_user(message.from_user)
    
    # Проверка на администратора
    if message.from_user.id != ADMIN_ID:
        await message.answer(f"⛔ У вас нет прав администратора! Ваш ID: `{message.from_user.id}` (добавьте его в переменную ADMIN_ID в коде).")
        return
        
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, registered_at FROM users")
    all_users = cursor.fetchall()
    conn.close()
    
    response = "👑 **Список всех пользователей:**\n\n"
    for u in all_users:
        response += f"• `{u[0]}` | @{u[1]} | {u[2]} (зарегистрирован: {u[3]})\n"
        
    await message.answer(response)

async def main():
    # Инициализируем базу данных при запуске
    init_db()
    
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
