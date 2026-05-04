from pydantic_settings import BaseSettings

#Configuration
class Settings(BaseSettings):

    #AppInfo
    APP_NAME: str = "Local-RAG"
    APP_VERSION: str = "0.1.0"

    # File Handling
    FILE_ALLOWED_EXTENSIONS: list = [
        "text/plain",
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    FILE_MAX_SIZE_MB: int = 5
    FILE_CHUNK_SIZE: int = 1048576  # 1 MB max bytes per read chunk

    #MongoDB
    MONGODB_URI: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "Local-RAG"

    # Generation LLM
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = ""
    GENERATE_RESPONSE_MODEL: str = ""

    #Embeddings
    EMBEDDINGS_MODEL: str = "BAAI/bge-small-en"
    EMBEDDING_DIMENSION: int = 384

    #Generation Settings
    MAX_INPUT_TOKENS: int = 200
    MAX_RESPONSE_TOKENS: int = 300
    TEMPERATURE: float = 0.1

    #Vector DB
    VECTOR_DB_PATH: str = "chroma_data"
    VECTOR_DB_DISTANCE_METRIC: str = "cosine"

    #Language
    DEFAULT_LANGUAGE: str = "en"

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Create new Settings instance"""
    return Settings()
