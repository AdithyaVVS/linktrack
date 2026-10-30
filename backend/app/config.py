from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    base_url: str = "http://127.0.0.1:8000"
    create_rate_limit: str = "10/minute"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
