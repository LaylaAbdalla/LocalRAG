"""
DataController Validates uploaded files before saving
Checks MIME type against the allowed list and enforces
the maximum file size from application settings.
"""

from fastapi import UploadFile
from controllers.BaseController import BaseController


class DataController(BaseController):
    """
    Responsible for upload validation only.
    Called by the data upload route before writing the file to disk.
    """

    def __init__(self):
        super().__init__()

    def validate_file(self, file: UploadFile) -> tuple[bool, str]:
        """
        Validate an uploaded file against allowed types and size limits.

        Args:
            file: FastAPI UploadFile instance from the request.

        Returns:
            isvalid message True success if valid
            False error description otherwise
        """
        # Check MIME type
        if file.content_type not in self.app_settings.FILE_ALLOWED_EXTENSIONS:
            return False, (
                f"Invalid file type: '{file.content_type}'. "
                f"Allowed: {self.app_settings.FILE_ALLOWED_EXTENSIONS}"
            )

        # Check file size
        max_bytes = self.app_settings.FILE_MAX_SIZE_MB * 1024 * 1024
        if file.size is not None and file.size > max_bytes:
            return False, (
                f"File size ({file.size / (1024*1024):.1f} MB) exceeds "
                f"the {self.app_settings.FILE_MAX_SIZE_MB} MB limit."
            )

        return True, "success"
