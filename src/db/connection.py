import asyncio
import logging
from contextlib import asynccontextmanager
from functools import wraps
from typing import Optional

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from settings import DatabaseSettings

logger = logging.getLogger(__name__)


class MongoDBManager:
    """Async MongoDB connection manager using Motor."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        settings: DatabaseSettings | None = None,
        max_pool_size: int = 100,
        min_pool_size: int = 10,
    ):
        if not hasattr(self, 'initialized'):
            self.settings = settings or DatabaseSettings()
            self.uri = self.settings.get_mongodb_uri()
            self.db_name = self.settings.MONGO_DB
            self.client: Optional[AsyncIOMotorClient] = None
            self.db: Optional[AsyncIOMotorDatabase] = None
            self._lock = asyncio.Lock()

            # Connection parameters
            self.connection_params = {
                'maxPoolSize': max_pool_size,
                'minPoolSize': min_pool_size,
                'connectTimeoutMS': 5000,
                'serverSelectionTimeoutMS': 5000,
                'retryWrites': True,
                'appname': 'OmnichannelSupport',
            }
            self.initialized = True
            self.is_connected = False

            safe_uri = self._get_safe_uri()

    def _get_safe_uri(self) -> str:
        """Returns a sanitized version of the URI for logging."""
        if self.settings.MONGO_USER and self.settings.MONGO_PASSWORD:
            return f'mongodb://<username>:xxxxx@{self.settings.MONGO_HOST}:{self.settings.MONGO_PORT}/{self.settings.MONGO_DB}'
        return self.uri

    async def connect(self) -> None:
        """Establish connection to MongoDB if not already connected."""
        if not self.is_connected:
            try:
                async with self._lock:
                    if not self.is_connected:  # Double-check after acquiring lock
                        logger.info(f'Connecting to MongoDB at {self.uri}')
                        self.client = AsyncIOMotorClient(self.uri, **self.connection_params)

                        # Test the connection
                        await self.client.admin.command('ping')

                        self.db = self.client[self.db_name]
                        self.is_connected = True
                        logger.info('Successfully connected to MongoDB')
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f'Failed to connect to MongoDB: {str(e)}')
                self.client = None
                self.db = None
                self.is_connected = False
                raise HTTPException(status_code=503, detail=f'Database connection failed: {str(e)}')
            except Exception as e:
                logger.error(f'Unexpected error connecting to MongoDB: {str(e)}')
                self.client = None
                self.db = None
                self.is_connected = False
                raise HTTPException(status_code=503, detail=f'Unexpected database error: {str(e)}')

    async def close(self) -> None:
        """Close the MongoDB connection if it exists."""
        if self.client is not None:
            async with self._lock:
                if self.client is not None:
                    logger.info('Closing MongoDB connection')
                    self.client.close()
                    self.client = None
                    self.db = None
                    self.is_connected = False

    async def get_db(self) -> AsyncIOMotorDatabase:
        """Get database instance, establishing connection if necessary."""
        if not self.is_connected:
            await self.connect()
        return self.db

    async def check_connection(self) -> bool:
        """Check if the database connection is alive."""
        try:
            if self.client:
                await self.client.admin.command('ping')
                return True
            return False
        except Exception:
            return False

    @asynccontextmanager
    async def get_connection(self):
        """Context manager for database connections."""
        if not self.is_connected:
            await self.connect()
        try:
            yield self.db
        except Exception as e:
            logger.error(f'Database operation failed: {str(e)}')
            raise
        finally:
            # Don't close the connection here, as we're using connection pooling
            pass


# Dependency for FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    db_manager = MongoDBManager()
    return await db_manager.get_db()


# Application startup and shutdown events
async def connect_to_mongodb():
    """Connect to MongoDB on application startup."""
    db_manager = MongoDBManager()
    await db_manager.connect()


async def close_mongodb_connection():
    """Close MongoDB connection on application shutdown."""
    db_manager = MongoDBManager()
    await db_manager.close()
