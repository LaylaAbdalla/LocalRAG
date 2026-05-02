import httpx
from stores.llm.LLMInterface import LLMInterface
from helpers.config import get_settings

class OllamaProvider(LLMInterface):
    def __init__(self):
        settings = get_settings()
        # Default to localhost if OPENAI_API_BASE is not set to Ollama
        self.base_url = settings.OPENAI_API_BASE if settings.OPENAI_API_BASE and "11434" in settings.OPENAI_API_BASE else "http://localhost:11434/api"
        # If the base URL ends with /v1 (OpenAI compatible), strip it for native Ollama API
        if self.base_url.endswith("/v1"):
            self.base_url = self.base_url[:-3] + "/api"
            
        self.generation_model = settings.GENERATE_RESPONSE_MODEL

    def set_generation_model(self, model_id: str):
        self.generation_model = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int = 0):
        pass # Not used for embedding in this implementation

    async def generate_response(self, prompt: str, chat_history: list = [], max_tokens: int = 500, temperature: float = 0.1) -> str | None:
        try:
            messages = chat_history.copy()
            if prompt:
                messages.append(self.construct_prompt(prompt, "user"))

            payload = {
                "model": self.generation_model,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens
                }
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/chat",
                    json=payload,
                    timeout=120.0
                )
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content")
                
        except Exception as e:
            print(f"Ollama Generation Error: {e}")
            return None

    async def embed_text(self, text: str, document_type: str = "") -> list[float] | None:
        raise NotImplementedError("OllamaProvider is only used for generation in this architecture.")

    def construct_prompt(self, prompt: str, role: str) -> dict:
        return {"role": role, "content": prompt}
