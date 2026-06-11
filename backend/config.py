import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    database_url: str = "mysql+mysqlconnector://root:@127.0.0.1:3306/university_erp"
    groq_api_key: str = "YOUR_GROQ_API_KEY_HERE"
    groq_model: str = "llama-3.3-70b-versatile"
    redis_url: Optional[str] = None
    api_rate_limit: str = "10/minute"
    port: int = 8000
    host: str = "127.0.0.1"

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(__file__), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
