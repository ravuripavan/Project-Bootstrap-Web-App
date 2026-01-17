from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

# SQLite doesn't support some PostgreSQL-specific options
engine_kwargs = {
    "echo": settings.debug,
}

# Only add pool_pre_ping for non-SQLite databases
if not settings.database_url.startswith("sqlite"):
    engine_kwargs["pool_pre_ping"] = True
else:
    # SQLite needs check_same_thread=False for async
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **engine_kwargs)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
