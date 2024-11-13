from aiogram import Router, types
from aiogram.filters import Command

router = Router(name=__name__)


@router.message(Command('start'))
async def start_command_handler(message: types.Message):
    await message.reply("Привет! Я могу показать твой ID. Просто напиши любое сообщение.")


@router.message()
async def get_group_id(message: types.Message):
    await message.reply(f"Твой ID: {message.chat.id}")
