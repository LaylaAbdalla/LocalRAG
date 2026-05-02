"""
ProjectModel CRUD operations for the projects MongoDB collection
Handles creating, retrieving, and listing projects.
"""

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from models.DataBaseModel import DataBaseModel
from models.db_schemes.project import Project


class ProjectModel(DataBaseModel):
    """
    Data access object for the 'projects' collection.
    Inherits the db_client from DataBaseModel.
    """

    def __init__(self, db_client: AsyncIOMotorClient):
        super().__init__(db_client)
        self.collection = self.db_client["projects"]

    async def create_project(self, project_id: str) -> Project:
        """
        Insert a new project document into MongoDB.

        Args:
            project_id: alphanumeric project identifier.

        Returns:
            The created Project with its new ObjectId.
        """
        project_data = {"project_id": project_id}
        result = await self.collection.insert_one(project_data)
        project_data["_id"] = result.inserted_id
        return Project(**project_data)

    async def get_project(self, project_id: str) -> Project | None:
        """
        Find a project by its project_id string.

        Returns:
            Project instance if found, None otherwise.
        """
        record = await self.collection.find_one({"project_id": project_id})
        if record is None:
            return None
        return Project(**record)

    async def get_project_or_create_one(self, project_id: str) -> Project:
        """
        Upsert pattern return existing project or create a new one
        Makes the upload endpoint idempotent: callers don't need to
        check whether the project already exists.

        Args:
            project_id: alphanumeric project identifier.

        Returns:
            The existing or newly created Project.
        """
        project = await self.get_project(project_id)
        if project is not None:
            return project
        return await self.create_project(project_id)

    async def get_all_projects(self) -> list[Project]:
        """Return all projects in the collection."""
        projects = []
        cursor = self.collection.find({})
        async for record in cursor:
            projects.append(Project(**record))
        return projects
