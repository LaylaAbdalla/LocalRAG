"""
DataChunk RetrievalDocument Pydantic schemas for chunk storage and search results

DataChunk: represents a text chunk stored in MongoDB's 'chunks' collection.
RetrievalDocument: lightweight search result returned from vector similarity queries.
"""

from pydantic import BaseModel, Field
from bson import ObjectId


class DataChunk(BaseModel):
    """
    Schema for a document in the 'chunks' MongoDB collection.

    Fields:
        id                MongoDB ObjectId aliased from id
        chunk_text        : the actual text content of this chunk
        chunk_metadata    : metadata dict (source file, page number, etc.)
        chunk_order       : integer position of this chunk within the document
        chunk_project_id  : ObjectId referencing the parent project
    """

    id: ObjectId = Field(None, alias="_id")
    chunk_text: str
    chunk_metadata: dict = {}
    chunk_order: int = 0
    chunk_project_id: ObjectId = None

    class Config:
        arbitrary_types_allowed = True
        populate_by_name = True


class RetrievalDocument(BaseModel):
    """
    Lightweight search result returned from vector similarity queries

    Fields:
        text  : the retrieved chunk text
        score : similarity score (cosine / dot product)
    """

    text: str
    score: float
