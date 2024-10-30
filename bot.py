import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Загрузка токена бота из .env файла
load_dotenv('.env')
BOT_TOKEN = os.getenv('BOT_TOKEN')

async def start_command_handler(message: types.Message):
    await message.reply("Привет! Я могу показать ID этой группы. Просто напишите любое сообщение.")

async def get_group_id(message: types.Message):
    if message.chat.type in ['group', 'supergroup']:
        await message.reply(f"ID этой группы: {message.chat.id}")

async def main():
    # Создаем экземпляры Bot и Dispatcher
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Регистрация обработчиков команд
    dp.message.register(start_command_handler, Command('start'))
    dp.message.register(get_group_id)

    # Запускаем polling
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
