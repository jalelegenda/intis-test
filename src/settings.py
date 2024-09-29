from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str = Field(default="localhost")
    postgres_port: str = Field(default="5432")

    token_secret: str
    token_expiration: int
    algorithm: str = "HS256"

    @property
    def db_dsn(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.postgres_user}"
            f":{self.postgres_password}"
            f"@{self.postgres_host}"
            f":5432/{self.postgres_db}"
        )


settings = Settings()  # type: ignore[call-arg]
