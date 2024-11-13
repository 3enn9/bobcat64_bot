from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import session_maker
from database.models import Export
from database.orm_query import orm_add_export
from filters import ChatTypeFilter

router = Router(name=__name__)

router.message.filter(ChatTypeFilter(["group", "supergroup"]))


@router.message(F.text.startswith("!"))
async def info_from_chat(message: types.Message):
    if message.forward_from is None:
        text = message.text.split('!')[1]

        async with session_maker() as session:
            added_text_id = await orm_add_export(session, text=text)
            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅", callback_data=f"export_{added_text_id}")]
                ]
            )

            await message.reply(text='Нажми если выполнено', reply_markup=keyboard)


@router.callback_query(F.data.startswith('export_'))
async def handle_callback_query(callback_query: types.CallbackQuery):
    export_id = int(callback_query.data.split('_')[1])

    async with session_maker() as session:

        result = await session.execute(select(Export).filter(Export.id == export_id))
        export = result.scalars().first()

        if export:
            export.status = True

            await session.commit()

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="❌", callback_data=f"change_export_{export_id}")]
                ]
            )

            await callback_query.message.edit_text(
                "Выполнено, если нет, нажми на крестик!",
                reply_markup=keyboard
            )
        else:
            await callback_query.answer("Не найдено записи с таким ID", show_alert=True)


@router.callback_query(F.data.startswith('change_export_'))
async def handle_callback_query(callback_query: types.CallbackQuery):
    export_id = int(callback_query.data.split('_')[2])

    async with session_maker() as session:

        result = await session.execute(select(Export).filter(Export.id == export_id))
        export = result.scalars().first()

        if export:
            export.status = False

            await session.commit()

            keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="✅", callback_data=f"export_{export_id}")]
                ]
            )

            await callback_query.message.edit_text(
                "Нажми если выполнено",
                reply_markup=keyboard
            )
        else:
            await callback_query.answer("Не найдено записи с таким ID", show_alert=True)
