import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command

# В реальном проекте токен лучше выносить в .env файл
TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"

# Диспетчер и бот
dp = Dispatcher()

# Обработка команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я эхо-бот. Напиши мне что-нибудь!")

# Эхо-обработчик (повторяет любое текстовое сообщение)
@dp.message(F.text)
async def echo_message(message: types.Message):
    await message.answer(message.text)

async def main():
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())