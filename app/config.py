from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = Field(default="Expense Tracker API")
    ENVIRONMENT: str = Field(default="development")
    # Your existing database settings
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    
    # Your existing security settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    GEMINI_API_KEY: str
    
    # ─── ADD THESE AZURE FIELDS TO THE SETTINGS CLASS ───
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_NAME: str = "user-policy-documents"
    
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_API_KEY: str
    AZURE_SEARCH_INDEX_NAME: str = "enterprise-knowledge-base"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
