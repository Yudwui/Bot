import asyncio
import json
from datetime import datetime, timezone, timedelta
import re
from openai import AsyncOpenAI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

TELEGRAM_BOT_TOKEN = "8844284513:AAHB1BBs_nE8Zfu72EPomPa28EJtknKcoZI"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL_NAME = "llama3.2"

client = AsyncOpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL)
session = AiohttpSession(timeout=60.0)
bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
dp = Dispatcher()

# --- 1. Определение функций-инструментов (Tools) ---

def get_weather(city: str) -> str:
    """Возвращает текущую погоду для указанного города."""
    # Имитация погодного API
    mock_weather = {
        "москва": "+15°C, облачно с прояснениями",
        "санкт-петербург": "+12°C, небольшой дождь",
        "новосибирск": "+8°C, ясно",
    }
    city_norm = city.lower().strip()
    weather_info = mock_weather.get(city_norm, "+18°C, солнечно, ветер 3 м/с")
    return f"Погода в городе {city}: {weather_info}."

def get_time(timezone_name: str = "UTC") -> str:
    """Возвращает текущее системное время."""
    now = datetime.now()
    return f"Текущее местное время: {now.strftime('%H:%M:%S (%d.%m.%Y)')}."

def calculate(expression: str) -> str:
    """Безопасно вычисляет математическое выражение."""
    # Очищаем от недопустимых символов
    cleaned = re.sub(r"[^0-9+\-*/().\s]", "", expression)
    try:
        result = eval(cleaned, {"__builtins__": None}, {})
        return f"Результат вычисления: {result}"
    except Exception as e:
        return f"Ошибка при вычислении выражения: {e}"

# Карта сопоставления названий с реальными функциями
AVAILABLE_TOOLS = {
    "get_weather": get_weather,
    "get_time": get_time,
    "calculate": calculate
}

# --- 2. JSON-схема инструментов для LLM ---

tools_schema = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Получить текущую погоду в конкретном городе",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Название города, например 'Москва'"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Получить текущее время",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone_name": {"type": "string", "description": "Часовой пояс или город"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Вычислить значение математического выражения (например: 25 * 40 - 15)",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Математическое выражение"}
                },
                "required": ["expression"]
            }
        }
    }
]

# --- 3. Логика агентного цикла ---

async def run_agent(user_query: str) -> str:
    """Агентный цикл: модель выбирает инструменты, мы их выполняем и возвращаем финальный ответ."""
    messages = [
        {
            "role": "system",
            "content": (
                "Ты AI-агент. Используй предоставленные инструменты (functions) при необходимости. "
                "Если для ответа на вопрос нужен расчет, погода или время — обязательно вызывай соответствующий инструмент. "
                "Отвечай на русском языке."
            )
        },
        {"role": "user", "content": user_query}
    ]

    # Цикл выполнения (поддержка нескольких вызовов подряд)
    for _ in range(5):
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            tools=tools_schema,
            tool_choice="auto"
        )

        response_message = response.choices[0].message
        messages.append(response_message)

        # Если модель не запросила вызов функций — возвращаем текстовый ответ
        if not response_message.tool_calls:
            return response_message.content or "Готово!"

        # Если модель запросила вызов инструментов
        for tool_call in response_message.tool_calls:
            func_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)

            print(f"🔧 Агент вызывает инструмент: {func_name}({args})")

            # Вызываем соответствующую функцию
            tool_func = AVAILABLE_TOOLS.get(func_name)
            if tool_func:
                tool_result = tool_func(**args)
            else:
                tool_result = f"Ошибка: неизвестный инструмент {func_name}"

            # Возвращаем результат в контекст модели
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result)
            })

    return "Превышен лимит вызовов инструментов."

# --- 4. Обработчики Telegram ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот-агент с вызовом инструментов (Tool Calling).\n\n"
        "Я умею:\n"
        "🌤 Узнавать погоду (`Какая погода в Москве?`)\n"
        "⏰ Говорить текущее время (`Который сейчас час?`)\n"
        "🧮 Считать сложные выражения (`Сколько будет 145 * 38 + 290?`)\n"
        "🔄 Решать комбинированные задачи (`Сколько будет 50 * 4 и какая погода в Новосибирске?`)"
    )

@dp.message()
async def handle_agent_message(message: types.Message):
    if not message.text:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    try:
        answer = await run_agent(message.text)
        await message.answer(answer)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка выполнения: {e}")

async def main():
    print("Агентный бот (Tool Calling) запущен в Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())