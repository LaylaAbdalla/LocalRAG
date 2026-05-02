"""
DataBaseModel Base class for all MongoDB model classes
Stores the async Motor database client and app settings.
Every model that performs MongoDB operations inherits from this.
"""

from motor.motor_asyncio import AsyncIOMotorClient
from helpers.config import Settings, get_settings


class DataBaseModel:
    """
    Root data-access class.
    Provides:
        - db_client    : a Motor async database handle
        - app_settings : loaded Settings instance
    """

    def __init__(self, db_client: AsyncIOMotorClient):
        """
        Args:
            db_client: an already-connected Motor database instance
                       (e.g. motor_client["Local-RAG"]).
        """
        self.db_client = db_client
        self.app_settings: Settings = get_settings()
