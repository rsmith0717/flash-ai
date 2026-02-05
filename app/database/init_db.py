from fastapi import Depends
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.database.db import Base
from app.models.user import User

# OLD Create the SQLAlchemy engine using the database URL from config
# engine = create_async_engine(settings.database_url)

# Create the asynchronous engine
# Connection pooling is managed automatically by the engine's configuration
engine = create_async_engine(url=settings.database_url, echo=True)

# OLD Create a configured "SessionLocal" class
# AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)

# Configure the sessionmaker for creating sessions within requests/tasks
AsyncSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
)


async def create_tables():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_db)):
    yield SQLAlchemyUserDatabase(session, User)
