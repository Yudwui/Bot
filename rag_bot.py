import os
import glob
import asyncio
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from openai import AsyncOpenAI
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.client.session.aiohttp import AiohttpSession

# 1. Настройки Telegram и локальной Ollama
TELEGRAM_BOT_TOKEN = "8844284513:AAHB1BBs_nE8Zfu72EPomPa28EJtknKcoZI"
OLLAMA_BASE_URL = "http://localhost:11434/v1"
MODEL_NAME = "llama3.2"

# 2. Инициализация модели эмбеддингов
print("Загрузка модели эмбеддингов...")
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

chunks = []
sources = []


def build_vector_database(docs_dir="docs"):
    """Чтение документов, разбиение на блоки и построение FAISS индекса."""
    txt_files = glob.glob(os.path.join(docs_dir, "*.txt"))
    if not txt_files:
        raise ValueError(
            f"Папка {docs_dir} пуста или не найдена. Создайте текстовые файлы в ней."
        )

    for filepath in txt_files:
        filename = os.path.basename(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        raw_chunks = [p.strip() for p in content.split("\n") if p.strip()]
        for chunk in raw_chunks:
            chunks.append(chunk)
            sources.append(filename)

    embeddings = embed_model.encode(chunks, convert_to_numpy=True)
    embeddings = np.array(embeddings, dtype="float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    print(f"База знаний готова! Загружено фрагментов: {len(chunks)}")
    return index


# Создаем векторный индекс при старте
faiss_index = build_vector_database()


def search_relevant_context(query: str, top_k: int = 2):
    """Поиск наиболее подходящих фрагментов по запросу."""
    query_vector = embed_model.encode([query], convert_to_numpy=True)
    query_vector = np.array(query_vector, dtype="float32")

    distances, indices = faiss_index.search(query_vector, top_k)

    found_contexts = []
    found_sources = set()

    for idx in indices[0]:
        if idx != -1:
            found_contexts.append(chunks[idx])
            found_sources.add(sources[idx])

    context_str = "\n".join(found_contexts)
    sources_str = ", ".join(found_sources)
    return context_str, sources_str


# 3. Инициализация клиента LLM и Telegram бота с увеличенным таймаутом
client = AsyncOpenAI(api_key="ollama", base_url=OLLAMA_BASE_URL)
session = AiohttpSession(timeout=60.0)
bot = Bot(token=TELEGRAM_BOT_TOKEN, session=session)
dp = Dispatcher()


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "Привет! Я RAG-бот по внутренней документации.\n"
        "Задай мне вопрос по материалам (например: «Зачем нужен break?» или «Что нового в aiogram 3?»), "
        "и я отвечу строго по документам с указанием источника!"
    )


@dp.message()
async def rag_query_handler(message: types.Message):
    if not message.text:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    user_query = message.text

    # 1. Извлекаем подходящий контекст из векторной базы
    context, sources_found = search_relevant_context(user_query, top_k=2)

    # 2. Формируем системный промпт со строгим контекстом
    system_prompt = (
        "Ты помощник, который отвечает на вопросы СТРОГО на основе предоставленного контекста.\n"
        "Отвечай на русском языке.\n"
        "Не придумывай ничего от себя. Если в контексте нет ответа, так и скажи.\n"
        f"КОНТЕКСТ:\n{context}"
    )

    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_query},
            ],
            temperature=0.2,
        )

        answer_text = response.choices[0].message.content
        final_message = f"{answer_text}\n\n📄 **Источник:** `{sources_found}`"
        await message.answer(final_message, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"⚠️ Ошибка обработки: {e}")


async def main():
    print("RAG-бот запущен в Telegram...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())