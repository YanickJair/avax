from typing import Optional
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    MONGO_HOST: str
    MONGO_PORT: int
    MONGO_DB: str
    MONGO_USER: str
    MONGO_PASSWORD: str
    MONGO_AUTH_SOURCE: Optional[str] = 'admin'

    def get_mongodb_uri(self) -> str:
        """Constructs the MongoDB URI based on the configuration."""
        # Base URI parts
        if self.MONGO_USER and self.MONGO_PASSWORD:
            # Authenticated connection
            credentials = f'{quote_plus(self.MONGO_USER)}:{quote_plus(self.MONGO_PASSWORD)}@'
            auth_source = f'?authSource={self.MONGO_AUTH_SOURCE}'
        else:
            # Non-authenticated connection
            credentials = ''
            auth_source = ''

        # Construct the URI
        uri = f'mongodb://{credentials}{self.MONGO_HOST}:{self.MONGO_PORT}/{self.MONGO_DB}{auth_source}'
        return uri

    class Config:
        env_file = '.env'
