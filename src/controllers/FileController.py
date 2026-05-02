"""
FileController Manages project specific directories under assets files
Creates folders on demand so each projects documents are isolated
"""

import os
from controllers.BaseController import BaseController


class FileController(BaseController):
    """
    Resolves and creates project upload directories.
    Each project gets its own folder at: assets/files/<project_name>/
    """

    def __init__(self):
        super().__init__()

    def get_file_path(self, dir_name: str) -> str:
        """
        Return the full directory path for a project's files.
        Creates the directory tree if it doesn't exist.

        Args:
            dir_name: project identifier (used as folder name).

        Returns:
            Absolute path to the project file directory.
        """
        project_dir = os.path.join(self.file_dir, dir_name)
        os.makedirs(project_dir, exist_ok=True)
        return project_dir

    def get_all_project_files(self, dir_name: str) -> list[str]:
        """
        List all files stored in a project's upload directory.

        Args:
            dir_name: project identifier.

        Returns:
            List of filenames in the project directory, or empty list.
        """
        project_dir = os.path.join(self.file_dir, dir_name)
        if not os.path.exists(project_dir):
            return []
        return [
            f for f in os.listdir(project_dir)
            if os.path.isfile(os.path.join(project_dir, f))
        ]
