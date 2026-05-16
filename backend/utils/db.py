from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, DateTime, Integer, func
from datetime import datetime
from typing import AsyncGenerator

from config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class MediaRecord(Base):
    __tablename__ = "media_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    ipfs_cid: Mapped[str] = mapped_column(String(256), nullable=False)
    wallet_address: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
    tx_signature: Mapped[str] = mapped_column(String(128), nullable=False)
    filename: Mapped[str] = mapped_column(String(256), nullable=True)
    phash: Mapped[str] = mapped_column(String(64), nullable=True)
    registered_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class VerificationLog(Base):
    __tablename__ = "verification_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    queried_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    similarity: Mapped[int] = mapped_column(Integer, nullable=False)
    deepfake_probability: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
