import os
import chromadb
from stores.vectordb.VectorDBInterface import VectorDBInterface
from helpers.config import get_settings
from models.db_schemes.data_chunk import RetrievalDocument

class ChromaDBProvider(VectorDBInterface):
    def __init__(self, **kwargs):
        settings = get_settings()
        self.db_path = os.path.join(settings.VECTOR_DB_PATH) # From settings
        self.client = None
        self.connect()

    def connect(self):
        """Establish connection to the local ChromaDB database."""
        # Using PersistentClient so the database is saved to disk
        self.client = chromadb.PersistentClient(path=self.db_path)
        print(f"Connected to ChromaDB at {self.db_path}")

    def create_collection(self, collection_name: str, embedding_size: int, distance_metric: str = "cosine"):
        """
        Create a new collection. 
        Chroma supports 'l2', 'ip', or 'cosine' distance metrics.
        """
        if distance_metric.lower() == "dot":
            distance_metric = "ip"
        elif distance_metric.lower() == "euclidean":
            distance_metric = "l2"
        else:
            distance_metric = "cosine"
            
        try:
            self.client.create_collection(
                name=collection_name,
                metadata={"hnsw:space": distance_metric}
            )
            print(f"Created collection {collection_name}")
        except Exception as e:
            # Collection might already exist
            print(f"Collection {collection_name} creation info: {e}")

    def add_documents(self, collection_name: str, documents: list, vectors: list[list[float]]):
        """Insert multiple documents and their embeddings into the collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
            
            # Prepare data
            ids = [str(doc.id) for doc in documents]
            texts = [doc.chunk_text for doc in documents]
            metadatas = [{k: str(v) for k, v in doc.chunk_metadata.items()} for doc in documents]
            
            collection.add(
                embeddings=vectors,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"Added {len(documents)} documents to {collection_name}")
            return True
        except Exception as e:
            print(f"Error adding documents to ChromaDB: {e}")
            return False

    def search_by_vector(self, collection_name: str, vector: list[float], top_k: int) -> list[RetrievalDocument]:
        """Search the collection using a query vector."""
        try:
            collection = self.client.get_collection(name=collection_name)
            results = collection.query(
                query_embeddings=[vector],
                n_results=top_k
            )
            
            retrieval_docs = []
            if results and 'documents' in results and results['documents']:
                # Chroma query returns a list of lists.
                docs = results['documents'][0]
                distances = results['distances'][0] if 'distances' in results else [0.0]*len(docs)
                
                for doc_text, distance in zip(docs, distances):
                    # For cosine distance, similarity is 1 - distance
                    # For L2, distance is the squared distance.
                    # We will just pass the score as is, though higher score meant higher similarity in Qdrant.
                    # So we will invert the distance to similarity for cosine.
                    score = 1.0 - distance if distance <= 1.0 else 1.0 / (1.0 + distance)
                    retrieval_docs.append(RetrievalDocument(text=doc_text, score=score))
                    
            return retrieval_docs
        except Exception as e:
            print(f"Error searching ChromaDB: {e}")
            return []

    def has_collection(self, collection_name: str) -> bool:
        """Check if a collection exists."""
        try:
            # list_collections returns a list of Collection objects or names
            collections = self.client.list_collections()
            return any(c.name == collection_name for c in collections)
        except Exception:
            return False

    def delete_collection(self, collection_name: str):
        """Delete an existing collection."""
        try:
            self.client.delete_collection(name=collection_name)
            print(f"Deleted collection {collection_name}")
        except Exception as e:
            print(f"Error deleting collection: {e}")
