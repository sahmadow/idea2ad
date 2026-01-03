from prisma import Prisma
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

db = Prisma()


async def connect_db():
    """Connect to database"""
    try:
        await db.connect()
        logger.info("Database connected")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise


async def disconnect_db():
    """Disconnect from database"""
    try:
        await db.disconnect()
        logger.info("Database disconnected")
    except Exception as e:
        logger.error(f"Database disconnect failed: {e}")


async def get_db() -> Prisma:
    """Dependency for getting database client"""
    return db


@asynccontextmanager
async def get_db_context():
    """Context manager for database operations"""
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
