from abc import ABC, abstractmethod
from typing import Any

class LLMInterface(ABC):
    """
    Abstract Base Class defining the contract for all LLM and Embedding providers.
    """
    
    @abstractmethod
    def set_generation_model(self, model_id: str):
        pass

    @abstractmethod
    def set_embedding_model(self, model_id: str, embedding_size: int):
        pass

    @abstractmethod
    def generate_response(self, prompt: str, chat_history: list = [], max_tokens: int = 500, temperature: float = 0.1) -> str | None:
        """
        Generate a text response based on the prompt.
        """
        pass

    @abstractmethod
    def embed_text(self, text: str, document_type: str = "") -> list[float] | None:
        """
        Convert text into vector embeddings. 
        document_type can be 'query' or 'document' for asymmetric embeddings.
        """
        pass

    @abstractmethod
    def construct_prompt(self, prompt: str, role: str) -> dict:
        """
        Construct a structured prompt dictionary (e.g., {"role": role, "content": prompt}).
        """
        pass
