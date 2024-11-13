from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Export


async def orm_add_export(session, text: str) -> int:
    # Создаем новый объект для таблицы Export
    new_export = Export(text=text)
    session.add(new_export)

    # Сохраняем объект в базе данных
    await session.commit()

    # Обновляем new_export, чтобы получить id после commit
    await session.refresh(new_export)

    # Возвращаем id добавленного объекта
    return new_export.id


