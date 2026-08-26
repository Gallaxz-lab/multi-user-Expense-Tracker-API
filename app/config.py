from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # System Orchestration Settings
    APP_NAME: str = Field(default="Expense Tracker API")
    ENVIRONMENT: str = Field(default="development")
    
    # Core Database Variables
    DB_USER: str = Field(default="postgres")
    DB_PASSWORD: str
    DB_HOST: str = Field(default="127.0.0.1")
    DB_PORT: int = Field(default=5432)
    DB_NAME: str
    
    # Internal Authentication/Security Setup
    SECRET_KEY: str
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    
    # Computed Dynamic Connection Properties
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # Auto-read mapping directly from root .env 
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8", 
        extra="ignore"
    )

settings = Settings()
