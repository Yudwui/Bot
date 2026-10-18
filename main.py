import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# Токен вашего бота
TOKEN = "8844284513:AAHB1BBs_nE8Zfu72EPomPa28EJtknKcoZI"

# Инициализируем хранилище состояний в памяти
dp = Dispatcher(storage=MemoryStorage())

# Описываем шаги состояний для опросника (FSM)
class SurveyStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_age = State()
    waiting_for_occupation = State()

# Команда /start запускает опрос
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear() # Сбрасываем старые состояния, если были
    builder = ReplyKeyboardBuilder()
    builder.button(text="/cancel")
    
    await message.answer(
        "Привет! Давайте пройдем небольшой опрос.\n"
        "Как вас зовут?\n\n"
        "*(Вы можете в любой момент прервать опрос командой `/cancel`)*",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )
    # Переходим к состоянию ожидания имени
    await state.set_state(SurveyStates.waiting_for_name)

# Команда /cancel для прерывания опроса
@dp.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Опрос прерван. Чтобы начать заново, введите `/start`.",
        reply_markup=types.ReplyKeyboardRemove()
    )

# Получаем имя
@dp.message(SurveyStates.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        return # Если пользователь ввел команду вместо имени
        
    await state.update_data(name=message.text)
    await message.answer(f"Приятно познакомиться, {message.text}!\nСколько вам лет?")
    await state.set_state(SurveyStates.waiting_for_age)

# Получаем возраст
@dp.message(SurveyStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        return
        
    if not message.text.isdigit():
        await message.answer("⚠️ Пожалуйста, введите возраст цифрами:")
        return
        
    await state.update_data(age=message.text)
    await message.answer("Чем вы занимаетесь? (ваша профессия или увлечение):")
    await state.set_state(SurveyStates.waiting_for_occupation)

# Получаем сферу деятельности и подводим итоги
@dp.message(SurveyStates.waiting_for_occupation)
async def process_occupation(message: types.Message, state: FSMContext):
    if message.text.startswith("/"):
        return
        
    await state.update_data(occupation=message.text)
    
    # Получаем все сохраненные данные из памяти (FSM)
    data = await state.get_data()
    
    summary = (
        "✅ **Спасибо за прохождение опроса!**\n\n"
        f"👤 **Имя:** {data.get('name')}\n"
        f"🎂 **Возраст:** {data.get('age')}\n"
        f"💼 **Занятие:** {data.get('occupation')}"
    )
    
    await message.answer(summary, reply_markup=types.ReplyKeyboardRemove())
    # Очищаем состояние
    await state.clear()

async def main():
    bot = Bot(token=TOKEN)
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())