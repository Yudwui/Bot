import os
import logging
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application

# 1. Настройка мониторинга и логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(name)s - %(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 2. Получение настроек из переменных окружения (Environment Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
# Публичный URL вашего облачного приложения (например: https://my-bot.onrender.com)
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "https://your-domain.com")
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Сетевые параметры для веб-сервера внутри контейнера/сервера
WEB_SERVER_HOST = "0.0.0.0"
WEB_SERVER_PORT = int(os.getenv("PORT", 8080))

if not BOT_TOKEN:
    logger.error("Критическая ошибка: переменная окружения BOT_TOKEN не задана!")
    sys.exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Обработчики команд ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    await message.answer(
        "🚀 Привет! Этот бот успешно развёрнут в облаке и работает 24/7 в режиме Webhook!"
    )

@dp.message(Command("health"))
async def cmd_health(message: types.Message):
    """Эндпоинт мониторинга состояния сервиса."""
    await message.answer("Статус системы: OK (200) ✅\nРежим: Serverless / Webhook")

@dp.message()
async def echo_handler(message: types.Message):
    await message.answer(f"Облачный бот принял сообщение: {message.text}")

# --- Настройка жизненного цикла Webhook ---

async def on_startup(bot: Bot) -> None:
    logger.info(f"Регистрация Webhook в Telegram: {WEBHOOK_URL}")
    await bot.set_webhook(
        url=WEBHOOK_URL,
        drop_pending_updates=True
    )

async def on_shutdown(bot: Bot) -> None:
    logger.info("Удаление Webhook перед завершением работы...")
    await bot.delete_webhook()

def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()

    # Роут проверки доступности для облачных мониторингов (Health Check)
    async def health_check(request):
        return web.Response(text="OK", status=200)

    app.router.add_get("/", health_check)

    # Привязка обработчика входящих вебхуков от Telegram
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot
    )
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    logger.info(f"Запуск веб-сервера на порту {WEB_SERVER_PORT}...")
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)

if __name__ == "__main__":
    main()