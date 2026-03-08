from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""
    postgres_url: str = ""
    log_level: str = "INFO"
    scraper_delay_seconds: float = 2.0
    environment: str = "development"

    # API authentication
    api_key: str = ""
    api_key_enabled: bool = False

    # CORS
    cors_origins: str = ""

    # Request size limit (bytes) — default 1MB
    max_request_size: int = 1_048_576

    # GDPR: hash query names in screening_log
    hash_screening_queries: bool = False


settings = Settings()
