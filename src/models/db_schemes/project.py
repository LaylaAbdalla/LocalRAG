"""
Project Pydantic schema for MongoDB project documents

Each project is a lightweight record that associates a human-readable
project_id (used as directory name) with a MongoDB ObjectId.
"""

from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


class Project(BaseModel):
    """
    Schema for a document in the 'projects' MongoDB collection.

    Fields:
        id         MongoDB ObjectId aliased from id
        project_id : alphanumeric string used as the project folder name
    """

    id: ObjectId = Field(None, alias="_id")
    project_id: str

    # Validators

    @field_validator("project_id")
    @classmethod
    def project_id_must_be_alphanumeric(cls, v: str) -> str:
        """Ensure project_id is safe for use as a directory name."""
        # Allow letters, digits, hyphens, underscores
        cleaned = v.replace("-", "").replace("_", "")
        if not cleaned.isalnum():
            raise ValueError(
                "project_id must contain only letters, digits, hyphens, or underscores."
            )
        return v

    class Config:
        # Allow ObjectId and other arbitrary types
        arbitrary_types_allowed = True
        # Populate by field name AND alias
        populate_by_name = True
