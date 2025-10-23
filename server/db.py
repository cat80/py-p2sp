from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from .config import SQLALCHEMY_DATABASE_URL
from .models import Base

# Create an asynchronous engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

# Create a session factory for creating async sessions
AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def get_session() -> AsyncSession:
    """
    Dependency function to get an async database session.
    """
    async with AsyncSessionFactory() as session:
        yield session

async def create_db_and_tables():
    """
    Asynchronously creates all database tables defined in the models.
    This function should be called once when the application starts.
    """
    async with engine.begin() as conn:
        # Drop all tables first (for development purposes)
        # In production, you would use migrations (e.g., with Alembic)
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

async def close_engine():
    """
    Closes the database engine's connection pool.
    Should be called when the application is shutting down.
    """
    await engine.dispose()
