from abc import ABC, abstractmethod
from typing import Any

class VectorDBInterface(ABC):
    """
    Abstract Base Class defining the contract for Vector Database providers.
    """
    
    @abstractmethod
    def connect(self):
        """Establish connection to the vector database."""
        pass

    @abstractmethod
    def create_collection(self, collection_name: str, embedding_size: int, distance_metric: str):
        """Create a new collection/index."""
        pass

    @abstractmethod
    def add_documents(self, collection_name: str, documents: list, vectors: list[list[float]]):
        """Insert multiple documents and their embeddings into the collection."""
        pass

    @abstractmethod
    def search_by_vector(self, collection_name: str, vector: list[float], top_k: int) -> list[Any]:
        """Search the collection using a query vector."""
        pass

    @abstractmethod
    def has_collection(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        pass

    @abstractmethod
    def delete_collection(self, collection_name: str):
        """Delete an existing collection."""
        pass
