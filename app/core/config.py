from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    # MongoDB
    MONGODB_URI: str
    MONGODB_DB_NAME: str = "verif-ai"

    # Firebase
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_JSON: str
    FIREBASE_API_KEY: str # Web API Key for REST testing

    # Google AI
    GEMINI_API_KEY: str
    GOOGLE_API_KEY: str

    # LangChain / LangSmith
    LANGCHAIN_TRACING_V2: str = "false"
    LANGCHAIN_API_KEY: Optional[str] = None
    LANGCHAIN_PROJECT: str = "verif-ai-backend"

    # External
    GITHUB_TOKEN: str
    BRAVE_API_KEY: str

    # App
    ALLOWED_ORIGINS: str = "http://localhost:3000,https://verif-ai-frontend.vercel.app"
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    @property
    def firebase_creds_dict(self) -> dict:
        return json.loads(self.FIREBASE_CREDENTIALS_JSON)

settings = Settings()
