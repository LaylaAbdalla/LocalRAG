"""
ChunkModel CRUD operations for the chunks MongoDB collection
Handles bulk insertion, paginated retrieval, and deletion of text chunks.
"""

from bson import ObjectId
from pymongo import InsertOne
from motor.motor_asyncio import AsyncIOMotorClient
from models.DataBaseModel import DataBaseModel
from models.db_schemes.data_chunk import DataChunk


class ChunkModel(DataBaseModel):
    """
    Data access object for the 'chunks' collection.
    Uses bulk_write for efficient batch inserts.
    """

    def __init__(self, db_client: AsyncIOMotorClient):
        super().__init__(db_client)
        self.collection = self.db_client["chunks"]

    async def insert_many_chunks(
        self, chunks: list[DataChunk], batch_size: int = 100
    ) -> int:
        """
        Batch-insert chunks into MongoDB using bulk_write.
        Processes in batches to avoid memory issues with large documents.

        Args:
            chunks     : list of DataChunk objects to insert.
            batch_size : how many documents per bulk_write call.

        Returns:
            Total number of inserted documents.
        """
        total_inserted = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            operations = [
                InsertOne(
                    {
                        "chunk_text": chunk.chunk_text,
                        "chunk_metadata": chunk.chunk_metadata,
                        "chunk_order": chunk.chunk_order,
                        "chunk_project_id": chunk.chunk_project_id,
                    }
                )
                for chunk in batch
            ]
            result = await self.collection.bulk_write(operations)
            total_inserted += result.inserted_count

        return total_inserted

    async def get_chunks_by_project_id(
        self, project_id: ObjectId, page: int = 1, page_size: int = 50
    ) -> list[DataChunk]:
        """
        Paginated retrieval of chunks for a given project.

        Args:
            project_id : MongoDB ObjectId of the parent project.
            page       : page number (1-indexed).
            page_size  : number of chunks per page.

        Returns:
            List of DataChunk objects for the requested page.
        """
        skip = (page - 1) * page_size
        chunks = []

        cursor = (
            self.collection.find({"chunk_project_id": project_id})
            .sort("chunk_order", 1)
            .skip(skip)
            .limit(page_size)
        )

        async for record in cursor:
            chunks.append(DataChunk(**record))

        return chunks

    async def get_total_chunks_count(self, project_id: ObjectId) -> int:
        """
        Return the total number of chunks for a project.
        Useful for pagination and progress tracking.
        """
        return await self.collection.count_documents(
            {"chunk_project_id": project_id}
        )

    async def delete_chunks_by_project_id(self, project_id: ObjectId) -> int:
        """
        Delete all chunks belonging to a project.
        Used when re-processing with do_reset=1.

        Returns:
            Number of deleted documents.
        """
        result = await self.collection.delete_many(
            {"chunk_project_id": project_id}
        )
        return result.deleted_count
