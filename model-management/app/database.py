"""
MongoDB async database connection using Motor.

Provides connection management and database access utilities.
"""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


class Database:
    """MongoDB database connection manager."""

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    @classmethod
    async def connect(cls) -> None:
        """
        Connect to MongoDB database.

        Creates connection pool and verifies connectivity.
        """
        try:
            logger.info(f"Connecting to MongoDB at {settings.MONGODB_URI}")

            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                minPoolSize=settings.MONGODB_MIN_POOL_SIZE,
                maxPoolSize=settings.MONGODB_MAX_POOL_SIZE,
                serverSelectionTimeoutMS=5000,
            )

            # Verify connection
            await cls.client.admin.command("ping")

            cls.db = cls.client[settings.MONGODB_DB_NAME]

            # Create indexes
            await cls._create_indexes()

            logger.info(f"Connected to MongoDB database: {settings.MONGODB_DB_NAME}")

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    @classmethod
    async def disconnect(cls) -> None:
        """
        Disconnect from MongoDB database.

        Closes connection pool gracefully.
        """
        if cls.client:
            cls.client.close()
            cls.client = None
            cls.db = None
            logger.info("Disconnected from MongoDB")

    @classmethod
    async def _create_indexes(cls) -> None:
        """Create database indexes for optimal query performance."""
        if cls.db is None:
            return

        # AI Models collection indexes
        models_collection = cls.db.models
        await models_collection.create_index("name")
        await models_collection.create_index("version")
        await models_collection.create_index([("name", 1), ("version", 1)], unique=True)
        await models_collection.create_index("model_type")
        await models_collection.create_index("framework")
        await models_collection.create_index("tags")
        await models_collection.create_index("created_at")
        await models_collection.create_index("is_active")
        await models_collection.create_index("created_by")

        # Plugins collection indexes
        plugins_collection = cls.db.plugins
        await plugins_collection.create_index("name", unique=True)
        await plugins_collection.create_index("status")
        await plugins_collection.create_index("created_at")

        # Model versions collection indexes
        versions_collection = cls.db.model_versions
        await versions_collection.create_index("model_id")
        await versions_collection.create_index("version")
        await versions_collection.create_index([("model_id", 1), ("version", 1)], unique=True)
        await versions_collection.create_index("created_at")
        await versions_collection.create_index("status")

        logger.info("Database indexes created successfully")

    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """
        Get database instance.

        Returns:
            AsyncIOMotorDatabase: MongoDB database instance

        Raises:
            RuntimeError: If database is not connected
        """
        if cls.db is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")
        return cls.db

    @classmethod
    def get_collection(cls, name: str):
        """
        Get a specific collection from the database.

        Args:
            name: Collection name

        Returns:
            Collection instance
        """
        db = cls.get_db()
        return db[name]


# Dependency for FastAPI
async def get_database() -> AsyncIOMotorDatabase:
    """
    FastAPI dependency to get database instance.

    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
    """
    return Database.get_db()
