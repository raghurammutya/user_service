from shared_architecture.db.session import get_async_session, get_sync_session
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with get_async_session() as session:
        yield session

def get_sync_db() -> Session:
    """Get sync database session"""
    return get_sync_session()

# For backward compatibility
get_db = get_sync_db