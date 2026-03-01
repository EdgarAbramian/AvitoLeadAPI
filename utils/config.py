from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent
ENV_PATH = ROOT_DIR / '.env'


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    AUTOHUB_API_KEY: str

    REDIS_HOST: str = "localhost"
    REDIS_USER: Optional[str] = ""
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: Optional[str] = ""
    REDIS_DB: int = 0

    @property
    def redis_url(self, db_num: Optional[int] = None) -> str:
        """Redis URL"""
        db = db_num if db_num is not None else self.REDIS_DB

        auth_part = ""
        if self.REDIS_USER or self.REDIS_PASSWORD:
            from urllib.parse import quote_plus
            password_encoded = quote_plus(self.REDIS_PASSWORD)
            auth_part = f"{self.REDIS_USER}:{password_encoded}@"

        return f"redis://{auth_part}{self.REDIS_HOST}:{self.REDIS_PORT}/{db}"


config = Config()
