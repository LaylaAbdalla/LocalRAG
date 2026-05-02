from sentence_transformers import SentenceTransformer
from stores.llm.LLMInterface import LLMInterface
from helpers.config import get_settings

class EmbeddingProvider(LLMInterface):
    def __init__(self):
        settings = get_settings()
        self.embedding_model_id = settings.EMBEDDINGS_MODEL
        print(f"Loading local embedding model: {self.embedding_model_id}")
        self.model = SentenceTransformer(self.embedding_model_id)
        
    def set_generation_model(self, model_id: str):
        raise NotImplementedError("EmbeddingProvider does not support text generation.")

    def set_embedding_model(self, model_id: str, embedding_size: int = 384):
        self.embedding_model_id = model_id
        self.model = SentenceTransformer(self.embedding_model_id)

    async def generate_response(self, prompt: str, chat_history: list = [], max_tokens: int = 500, temperature: float = 0.1) -> str | None:
        raise NotImplementedError("EmbeddingProvider does not support text generation.")

    async def embed_text(self, text: str, document_type: str = "") -> list[float] | None:
        """
        Embeds text. 
        document_type can be 'query' or 'document' for models that support asymmetric embeddings.
        """
        try:
            prefix = "query: " if document_type == "query" else "passage: "
            # Many models like BGE benefit from a prefix
            full_text = prefix + text if self.embedding_model_id.lower().find("bge") != -1 else text
            
            embedding = self.model.encode(full_text)
            return embedding.tolist()
        except Exception as e:
            print(f"Local Embedding Error: {e}")
            return None

    def construct_prompt(self, prompt: str, role: str) -> dict:
        return {"role": role, "content": prompt}
