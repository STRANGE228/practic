from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "Kanban Board"
    DATABASE_URL: str = "sqlite:///./kanban.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()