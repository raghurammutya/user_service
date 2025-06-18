from shared_architecture.db.session import AsyncSessionLocal, SessionLocal
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session"""
    async with AsyncSessionLocal() as session:
        yield session

def get_sync_db() -> Session:
    """Get sync database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# For backward compatibility
get_db = get_sync_db