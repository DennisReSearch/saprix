import asyncio
import os
import random
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from telethon import TelegramClient

# === Укажите свои API_ID, API_HASH и токен бота ===
API_ID = 20199491  # Вставьте свой API ID
API_HASH = "fc95dbb20a664b9659dee52b65d124b1"  # Вставьте свой API HASH
BOT_TOKEN = "7269288490:AAGlD9a2U_Ii9UsUR2AfjhTYviWFDeNrHvA"  # Вставьте токен Telegram-бота
SESSION_FILE = "session"

# Папка проекта
PROJECT_DIR = "F:\TgBot"
USERNAMES_FILE = os.path.join(PROJECT_DIR, "usernames.txt")
MESSAGE_TEXT = "Привет, ты заливаешь трафик? Если да, то какие объемы и откуда?))"

# Настройка бота
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

def load_usernames():
    """Загрузка юзернеймов из файла"""
    if not os.path.exists(USERNAMES_FILE):
        return []
    with open(USERNAMES_FILE, 'r', encoding='utf-8') as file:
        return [line.strip() for line in file if line.strip()]

async def collect_users(client, chat_link):
    """Сбор активных пользователей из чата и сохранение в файл"""
    try:
        chat = await client.get_entity(chat_link)
    except Exception as e:
        return f"❌ Ошибка: {e}", []
    
    active_users = set()
    try:
        async for user in client.iter_participants(chat):
            if user.username:
                active_users.add(user.username)
    except Exception:
        async for message in client.iter_messages(chat, limit=1000):
            if message.sender_id:
                try:
                    user = await client.get_entity(message.sender_id)
                    if user.username:
                        active_users.add(user.username)
                except:
                    pass
    
    os.makedirs(PROJECT_DIR, exist_ok=True)
    with open(USERNAMES_FILE, "w", encoding="utf-8") as file:
        for username in sorted(active_users):
            file.write(f"@{username}\n")
    
    return f"✅ Найдено {len(active_users)} активных пользователей!", list(active_users)

async def send_messages(client):
    """Отправка сообщений пользователям"""
    usernames = load_usernames()
    count = 0
    for username in usernames:
        try:
            user = await client.get_entity(username)
            await client.send_message(user, MESSAGE_TEXT)
            count += 1
            await asyncio.sleep(random.randint(1, 30))
        except Exception:
            pass
    return f"✅ Рассылка завершена! Отправлено: {count} сообщений."

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    """Обработчик команды /start"""
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("📌 Собрать юзернеймы", callback_data="collect"),
        InlineKeyboardButton("📄 Показать список", callback_data="list"),
        InlineKeyboardButton("🚀 Начать рассылку", callback_data="send")
    )
    await message.answer("🔹 Телеграм бот для сбора и рассылки сообщений 🔹", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == 'collect')
async def collect_callback(callback_query: types.CallbackQuery):
    """Кнопка сбора пользователей"""
    await bot.send_message(callback_query.from_user.id, "Введите ссылку на чат:")
    chat_link = await bot.wait_for("message")
    
    async with TelegramClient(os.path.join(PROJECT_DIR, SESSION_FILE), API_ID, API_HASH) as client:
        result, _ = await collect_users(client, chat_link.text.strip())
    
    await bot.send_message(callback_query.from_user.id, result)

@dp.callback_query_handler(lambda c: c.data == 'list')
async def list_callback(callback_query: types.CallbackQuery):
    """Кнопка просмотра списка"""
    usernames = load_usernames()
    if not usernames:
        await bot.send_message(callback_query.from_user.id, "Список пуст.")
    else:
        await bot.send_message(callback_query.from_user.id, "\n".join(usernames[:50]))

@dp.callback_query_handler(lambda c: c.data == 'send')
async def send_callback(callback_query: types.CallbackQuery):
    """Кнопка начала рассылки"""
    async with TelegramClient(os.path.join(PROJECT_DIR, SESSION_FILE), API_ID, API_HASH) as client:
        result = await send_messages(client)
    await bot.send_message(callback_query.from_user.id, result)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
