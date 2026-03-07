from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"
    postgres_url: str = "postgresql://africapep:secret@localhost:5432/africapep"
    log_level: str = "INFO"
    scraper_delay_seconds: float = 2.0
    environment: str = "development"


settings = Settings()
