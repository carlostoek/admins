# telegram_subscription_bot/database/db.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager

from database.models import Base
from config import DATABASE_URL

# Convertir SQLite URL a formato async
if DATABASE_URL.startswith('sqlite'):
    DATABASE_URL = DATABASE_URL.replace('sqlite', 'sqlite+aiosqlite', 1)

engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def get_session():
    session = async_session()
    try:
        yield session
    finally:
        await session.close()