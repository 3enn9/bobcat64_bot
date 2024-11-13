import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from database.models import Base

load_dotenv()
DB_URL = os.getenv('DB_URL')
engine = create_async_engine(DB_URL, echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# async def get_session() -> AsyncSession:
#     # Здесь async_sessionmaker создает сессию, которая будет использована как контекстный менеджер
#     async with session_maker() as session:
#         yield session

