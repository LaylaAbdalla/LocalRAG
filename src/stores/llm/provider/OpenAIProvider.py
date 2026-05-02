import os
from openai import AsyncOpenAI
from stores.llm.LLMInterface import LLMInterface
from helpers.config import get_settings

class OpenAIProvider(LLMInterface):
    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE if settings.OPENAI_API_BASE else None
        )
        self.generation_model = settings.GENERATE_RESPONSE_MODEL
        self.embedding_model = settings.EMBEDDINGS_MODEL

    def set_generation_model(self, model_id: str):
        self.generation_model = model_id

    def set_embedding_model(self, model_id: str, embedding_size: int = 1536):
        self.embedding_model = model_id

    async def generate_response(self, prompt: str, chat_history: list = [], max_tokens: int = 500, temperature: float = 0.1) -> str | None:
        try:
            messages = chat_history.copy()
            if prompt:
                messages.append(self.construct_prompt(prompt, "user"))

            response = await self.client.chat.completions.create(
                model=self.generation_model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"OpenAI Generation Error: {e}")
            return None

    async def embed_text(self, text: str, document_type: str = "") -> list[float] | None:
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"OpenAI Embedding Error: {e}")
            return None

    def construct_prompt(self, prompt: str, role: str) -> dict:
        return {"role": role, "content": prompt}
