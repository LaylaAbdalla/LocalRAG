"""
BaseController Parent class for all controllers
Provides shared application settings and filesystem path resolution
for file storage and database directories.
"""

import os
from helpers.config import Settings, get_settings


class BaseController:
    """
    Base class that every controller inherits from.
    Centralizes access to:
        - app_settings  : the loaded Settings instance
        - base_dir      : absolute path to the `src/` directory
        - file_dir      : absolute path to `src/assets/files/` (uploaded documents)
        - db_dir        : absolute path to `src/assets/db/`    (local DB storage)
    """

    def __init__(self):
        self.app_settings: Settings = get_settings()

        # Resolve paths relative to this files location
        self.base_dir = os.path.dirname(              # src folder
            os.path.dirname(os.path.abspath(__file__)) # src controllers folder
        )

        # Assets directories
        self.file_dir = os.path.join(self.base_dir, "assets", "files")
        self.db_dir   = os.path.join(self.base_dir, "assets", "db")

    def get_db_path(self, db_name: str) -> str:
        """
        Build and return the full path to a database subdirectory.
        Creates the directory if it doesn't already exist.

        Args:
            db_name: name of the database folder (e.g. 'chroma_data')

        Returns:
            Absolute path to the database directory.
        """
        db_path = os.path.join(self.db_dir, db_name)
        os.makedirs(db_path, exist_ok=True)
        return db_path
