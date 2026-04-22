from pathlib import Path

from pydantic_settings import BaseSettings


def _find_project_root() -> Path:
    return Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_URL: str = "http://localhost:8000"

    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000

    DB_DRIVER: str = "mysql"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_NAME: str = "UsuariosLegislaIA"
    DB_USER: str = "root"
    DB_PASS: str = ""
    DB_CHARSET: str = "utf8mb4"
    DB_DSN: str = ""

    SECRET_KEY: str = "change-me-in-production"
    SESSION_COOKIE_NAME: str = "legisla_session"
    SESSION_MAX_AGE: int = 86400  # 24h

    GEMINI_MODEL: str = "gemini-3.1-flash-lite-preview"
    GEMINI_API_KEY: str = ""

    LEGISLA_API_BASE_URL: str = "http://127.0.0.1:8000"

    model_config = {
        "env_file": str(_find_project_root() / ".env"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }

    @property
    def database_url(self) -> str:
        if self.DB_DSN:
            return self.DB_DSN

        if self.DB_DRIVER == "sqlite":
            return f"sqlite:///{self.DB_NAME}.db"

        if self.DB_DRIVER == "pgsql":
            return (
                f"postgresql://{self.DB_USER}:{self.DB_PASS}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )

        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASS}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )


settings = Settings()
