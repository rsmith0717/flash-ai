# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    # Tell Pydantic to load environment variables from .env
    model_config = SettingsConfigDict(env_file="api.env")


settings = Settings()
