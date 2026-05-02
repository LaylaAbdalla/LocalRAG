from stores.llm.LLMInterface import LLMInterface
from stores.llm.provider.OpenAIProvider import OpenAIProvider
from stores.llm.provider.EmbeddingProvider import EmbeddingProvider
from stores.llm.provider.OllamaProvider import OllamaProvider

class LLMFactory:
    """
    Factory class to instantiate LLM and Embedding providers.
    """
    
    @staticmethod
    def create(provider_type: str) -> LLMInterface:
        """
        Create and return an instance of the requested provider type.
        
        Args:
            provider_type: "openai", "local_bge", or "ollama"
            
        Returns:
            An implementation of LLMInterface.
        """
        if provider_type == "openai":
            return OpenAIProvider()
        elif provider_type == "ollama":
            return OllamaProvider()
        elif provider_type == "local_bge":
            return EmbeddingProvider()
        else:
            raise ValueError(f"Unknown LLM provider type: {provider_type}")
