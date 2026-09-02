from typing import List, Union, Any
from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, computed_field, ConfigDict, Field, field_validator

class Settings(BaseSettings):
    PROJECT_NAME: str = "Splitwise Clone"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = Field(..., min_length=32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "splitwise"
    POSTGRES_PORT: int = 5455
    DATABASE_URL: str | None = None
    POSTGRES_SSL_MODE: str = "disable"

    # We use Union/Any type here to prevent Pydantic from trying to JSON-parse the env var too early
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8000"]

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if v == "YOUR_SUPER_SECRET_KEY_HERE":
            raise ValueError("SECRET_KEY must not use the public placeholder")
        return v

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, str) and v.startswith("["):
            import json
            return json.loads(v)
        elif isinstance(v, list):
            return v
        return v


    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            url = self.DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            return url

        return str(PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )) + f"?sslmode={self.POSTGRES_SSL_MODE}"

    model_config = ConfigDict(case_sensitive=True, env_file=".env", extra="allow")

settings = Settings()
