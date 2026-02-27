from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


# ── Async Engine ──────────────────────────────────────────────────────────────
# pool_pre_ping=True: validates connections before using them (handles DB restarts)
# pool_size / max_overflow: controls concurrent DB connections
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    echo=not settings.is_production,   # logs SQL in development only
)

# ── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,     # keeps ORM objects accessible after commit
    autoflush=False,
    autocommit=False,
)


# ── Base Class ────────────────────────────────────────────────────────────────
# All SQLAlchemy models must inherit from this Base
class Base(DeclarativeBase):
    pass


# ── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides a DB session per request.
    Automatically commits on success and rolls back on exception.

    Usage in route:
        async def my_route(db: AsyncSession = Depends(get_db)):
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()