from sqlalchemy import String, Text, Float, Integer, DateTime, func, Numeric, ForeignKey, BigInteger, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Export(Base):
    __tablename__ = 'exports'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    text: Mapped[str] = mapped_column(String(150), nullable=False)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    status: Mapped[bool] = mapped_column(Boolean, default=False)


class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    first_name: Mapped[str] = mapped_column(String(150), nullable=True)
    last_name: Mapped[str] = mapped_column(String(150), nullable=True)
    # phone: Mapped[str] = mapped_column(String(13), nullable=True)
