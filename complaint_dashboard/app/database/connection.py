import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# SQLite database file path
DATABASE_URL = "sqlite+aiosqlite:///./complaints.db"

# Create async engine. Since we are using SQLite, we enable disable_check_same_thread for async operation compatibility.
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False
)

# Async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for SQLAlchemy models
class Base(DeclarativeBase):
    pass

# FastAPI Dependency to get database sessions
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Database initializer
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
