from stores.vectordb.VectorDBInterface import VectorDBInterface
from stores.vectordb.provider.ChromaDB import ChromaDBProvider

class VectorDBFactory:
    """
    Factory class to instantiate Vector DB providers.
    """
    
    @staticmethod
    def create(provider_type: str, **kwargs) -> VectorDBInterface:
        """
        Create and return an instance of the requested VectorDB provider type.
        
        Args:
            provider_type: "chromadb"
            **kwargs: Configuration arguments like path, url, etc.
            
        Returns:
            An implementation of VectorDBInterface.
        """
        if provider_type == "chromadb":
            return ChromaDBProvider(**kwargs)
        else:
            raise ValueError(f"Unknown Vector DB provider type: {provider_type}")
