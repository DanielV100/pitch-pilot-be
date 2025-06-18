"""
app/core/database.py
────────────────────────────────────────────────────────────────
• Creates a single async engine from the POSTGRES_URL in Settings
• Exposes `AsyncSession` factory (`async_session`)
• Provides `get_session` FastAPI dependency
• Exposes a sync engine (`sync_engine`) for Alembic migrations
"""

from __future__ import annotations

import contextlib
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

async_engine = create_async_engine(
    settings.POSTGRES_URL,
    echo=False,              
    pool_pre_ping=True,     
)

sync_engine = create_engine(
    settings.POSTGRES_URL.replace("+asyncpg", ""), 
    echo=False,
    pool_pre_ping=True,
)


async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,   
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield a transactional AsyncSession that is closed at the end of the request.

    Usage in routes / services:
        @router.get(...)
        async def list_things(db: AsyncSession = Depends(get_session)):
            ...
    """
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@contextlib.asynccontextmanager
async def lifespan(app):
    """Call in FastAPI(..., lifespan=lifespan) to cleanly dispose the engine."""
    yield
    await async_engine.dispose()
