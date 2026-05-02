"""
RequestProcess Pydantic schema for the file processing chunking request body

Sent as JSON to POST /api/data/process/projectid
"""

from pydantic import BaseModel, Field


class RequestProcess(BaseModel):
    """
    Request body for the chunking endpoint.

    Fields:
        file_name  : name of the file to process (must already be uploaded)
        chunk_size : max characters per chunk (default 100)
        overlap    : character overlap between consecutive chunks (default 20)
        do_reset   : if 1, delete existing chunks before re-processing
    """

    file_name: str
    chunk_size: int = Field(default=100, ge=10, le=10000)
    overlap: int = Field(default=20, ge=0)
    do_reset: int = Field(default=0, ge=0, le=1)
