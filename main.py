import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# Вставьте ваш токен от BotFather
TOKEN = "8844284513:AAHB1BBs_nE8Zfu72EPomPa28EJtknKcoZI"

dp = Dispatcher()

# 1. Обработка команды /start с обычной клавиатурой (Reply)
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Создаем обычную клавиатуру
    builder = ReplyKeyboardBuilder()
    builder.button(text="Привет")
    builder.button(text="Пока")
    builder.button(text="Помощь")
    builder.adjust(2) # Располагаем по 2 кнопки в ряду
    
    await message.answer(
        "Привет! Выберите действие на клавиатуре ниже:",
        reply_markup=builder.as_markup(resize_keyboard=True) # resize_keyboard делает кнопки аккуратнее
    )

# 2. Обработка нажатий на обычные кнопки
@dp.message(F.text == "Привет")
async def btn_hello(message: types.Message):
    await message.answer("И вам привет! Рад общению.")

@dp.message(F.text == "Пока")
async def btn_bye(message: types.Message):
    await message.answer("До свидания! Хорошего дня!")

@dp.message(F.text == "Помощь")
async def btn_help(message: types.Message):
    # Создаем инлайн-кнопки (под сообщением)
    builder = InlineKeyboardBuilder()
    builder.button(text="Перейти на GitHub", url="https://github.com")
    builder.button(text="Нажми меня", callback_data="inline_button_clicked")
    builder.adjust(1)
    
    await message.answer(
        "Это раздел помощи. Здесь есть инлайн-кнопки:",
        reply_markup=builder.as_markup()
    )

# 3. Обработка кликов по инлайн-кнопкам (callback_query)
@dp.callback_query(F.data == "inline_button_clicked")
async def inline_btn_handler(callback: types.CallbackQuery):
    # Убираем "часики" загрузки на кнопке в Telegram
    await callback.answer("Вы нажали инлайн-кнопку!", show_alert=True)
    await callback.message.answer("Отлично! Инлайн-кнопка успешно сработала.")

# 4. Эхо-обработчик для остальных сообщений
@dp.message(F.text)
async def echo_message(message: types.Message):
    await message.answer(f"Эхо: {message.text}")

async def main():
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())