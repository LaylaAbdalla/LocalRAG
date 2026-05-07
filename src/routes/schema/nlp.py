from pydantic import BaseModel, Field

class PushDataRequest(BaseModel):
    do_reset: int = Field(0, description="1 to reset/recreate collection, 0 otherwise")

class SearchRequest(BaseModel):
    text: str = Field(..., description="The query string")
    top_k: int = Field(5, description="Number of results to return")

class AnswerRequest(BaseModel):
    text: str = Field(..., description="The question for the RAG pipeline")
    top_k: int = Field(5, description="Number of context chunks to retrieve")
    lang: str = Field("en", description="Language for prompts, 'en' or 'ar'")
    model: str | None = Field(None, description="The LLM generation model to use")
