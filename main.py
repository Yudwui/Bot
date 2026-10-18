import asyncio
import logging
import time
import aiohttp
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Токен вашего бота
TOKEN = "8844284513:AAHB1BBs_nE8Zfu72EPomPa28EJtknKcoZI"

dp = Dispatcher()

# Кэш для курсов валют (храним 5 минут = 300 секунд)
cache = {
    "data": None,
    "timestamp": 0
}
CACHE_TTL = 300

async def get_exchange_rates():
    """Получает курсы валют с внешнего API с учетом кэширования на 5 минут"""
    current_time = time.time()
    if cache["data"] and (current_time - cache["timestamp"] < CACHE_TTL):
        return cache["data"]
    
    # Используем бесплатное открытое API для курсов валют
    url = "https://open.er-api.com/v6/latest/USD"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    cache["data"] = data.get("rates", {})
                    cache["timestamp"] = current_time
                    return cache["data"]
    except Exception as e:
        logging.error(f"Ошибка запроса к API: {e}")
    return None

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="USD -> RUB", callback_data="rate_USD_RUB")
    builder.button(text="EUR -> RUB", callback_data="rate_EUR_RUB")
    builder.button(text="EUR -> USD", callback_data="rate_EUR_USD")
    builder.adjust(2)
    
    await message.answer(
        "Привет! Я бот-конвертер валют.\n"
        "Используй команду в формате: `/rate USD RUB`\n"
        "Или выбери популярную пару на кнопках ниже:",
        reply_markup=builder.as_markup()
    )

@dp.message(Command("rate"))
async def cmd_rate(message: types.Message, command: CommandObject):
    if not command.args:
        await message.answer("⚠️ Пожалуйста, укажите валютную пару. Пример: `/rate USD RUB`")
        return
    
    args = command.args.upper().split()
    if len(args) != 2:
        await message.answer("⚠️ Неверный формат! Используйте два кода валют, например: `/rate USD RUB`")
        return
    
    base, target = args[0], args[1]
    rates = await get_exchange_rates()
    
    if not rates:
        await message.answer("❌ Не удалось получить данные от сервера валют. Попробуйте позже.")
        return
    
    if base not in rates or target not in rates:
        await message.answer(f"❌ Ошибка: одна из валют (`{base}` или `{target}`) не найдена или не поддерживается.")
        return
    
    # Расчет кросс-курса через USD
    try:
        base_rate = 1.0 if base == "USD" else rates.get(base)
        target_rate = 1.0 if target == "USD" else rates.get(target)
        
        result = target_rate / base_rate if base != "USD" else target_rate
        
        await message.answer(f"💱 Текущий курс: **1 {base} = {result:.4f} {target}**")
    except Exception:
        await message.answer("❌ Произошла ошибка при расчете курса.")

@dp.callback_query(F.data.startswith("rate_"))
async def inline_rate_handler(callback: types.CallbackQuery):
    _, base, target = callback.data.split("_")
    rates = await get_exchange_rates()
    
    if not rates:
        await callback.answer("Ошибка получения данных", show_alert=True)
        return
        
    base_rate = 1.0 if base == "USD" else rates.get(base)
    target_rate = 1.0 if target == "USD" else rates.get(target)
    result = target_rate / base_rate if base != "USD" else target_rate
    
    await callback.answer()
    await callback.message.answer(f"💱 Курс по кнопке: **1 {base} = {result:.4f} {target}**")

async def main():
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())