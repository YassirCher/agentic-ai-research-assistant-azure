from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Research Assistant"
    ENV: str = "dev"
    GROQ_API_KEY: str = ""
    CHROMA_PERSIST_DIR: str = "../data/chroma"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    CORS_ALLOW_ORIGINS: str = "http://localhost,http://127.0.0.1,http://localhost:3000,http://localhost:5173"
    
    # Modele Groq (Routing, Ranker, Critic) - Rapide & economique
    GROQ_FAST_MODEL: str = "llama3-8b-8192"
    
    # Modele Groq (Generator) - Plus intelligent
    GROQ_SMART_MODEL: str = "llama-3.3-70b-versatile"
    
    # Limites pour le RAG
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RETRIEVAL: int = 4
    EMBEDDING_BATCH_SIZE: int = 75
    EMBEDDING_BATCH_SLEEP_SECONDS: float = 0.05

    # Upload constraints
    MAX_UPLOAD_FILES: int = 10
    MAX_UPLOAD_FILE_MB: int = 25

    # API security controls
    RATE_LIMIT_QUERY: int = 20
    RATE_LIMIT_UPLOAD: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Groq budget controls
    TOKEN_BUDGET_TOTAL: int = 6000
    TOKEN_BUDGET_GENERATOR: int = 4200
    TOKEN_BUDGET_ROUTER_RANKER_CRITIC: int = 1200
    TOKEN_BUDGET_SAFETY_MARGIN: int = 600
    TOKEN_ESTIMATE_CHARS_PER_TOKEN: int = 4

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origins(self) -> List[str]:
        origins = [o.strip() for o in self.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
        if self.ENV.lower() == "prod":
            return origins
        dev_defaults = ["http://localhost:3000", "http://localhost:5173"]
        merged = origins + [o for o in dev_defaults if o not in origins]
        return merged

settings = Settings()
