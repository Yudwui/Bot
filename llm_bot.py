import asyncio
from collections import defaultdict
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from openai import AsyncOpenAI

# 1. Токен твоего Telegram-бота из BotFather
TELEGRAM_BOT_TOKEN = "8844284513:AAHB1BBs_nE8Zfu72EPomPa28EJtknKcoZI"

# 2. Подключение к локальной Ollama
client = AsyncOpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1"
)
MODEL_NAME = "llama3.2"

# 3. Хранилище контекста диалога (последние 10 сообщений = 5 пар вопрос-ответ)
dialog_history = defaultdict(list)
MAX_HISTORY_LENGTH = 10

bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я умный чат-бот на базе локальной LLM.\n"
        "Задай мне вопрос, я помню контекст диалога.\n"
        "Очистить историю: /clear"
    )


@dp.message(Command("clear"))
async def cmd_clear(message: types.Message):
    user_id = message.from_user.id
    if user_id in dialog_history:
        dialog_history[user_id].clear()
    await message.answer("🧹 История диалога очищена!")


@dp.message()
async def chat_with_llm(message: types.Message):
    if not message.text:
        return

    user_id = message.from_user.id

    # Добавляем сообщение пользователя в историю
    dialog_history[user_id].append({"role": "user", "content": message.text})

    # Ограничиваем историю диалога
    if len(dialog_history[user_id]) > MAX_HISTORY_LENGTH:
        dialog_history[user_id] = dialog_history[user_id][-MAX_HISTORY_LENGTH:]

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        messages_payload = [
            {"role": "system", "content": "Ты полезный ассистент. Отвечай на русском языке."}
        ] + dialog_history[user_id]

        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages_payload,
            temperature=0.7,
        )

        reply_text = response.choices[0].message.content
        dialog_history[user_id].append({"role": "assistant", "content": reply_text})

        await message.answer(reply_text)

    except Exception as e:
        await message.answer(f"⚠️ Ошибка генерации ответа: {e}")


async def main():
    print("Локальный LLM-бот запущен в Telegram...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())