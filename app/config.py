from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    APP_NAME: str = Field(default="Expense Tracker API")
    ENVIRONMENT: str = Field(default="development")
    
    # Live PostgreSQL Core Relational Store Credentials
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    
    # Active Application Encryption Configuration Parameters 
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    
    # Provider-Agnostic LLM Configuration Routing Mappings
    # Enforces choices: 'gemini', 'openai', or 'anthropic' without code rewrites
    LLM_PROVIDER: str = "gemini" 
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    
    # Managed Cloud Storage Infrastructure Pathways (Azure Blob Container)
    AZURE_STORAGE_CONNECTION_STRING: str
    AZURE_STORAGE_CONTAINER_NAME: str = "user-policy-documents"
    
    # Enterprise Cloud Vector Index Architecture Pathways (Azure AI Search)
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_API_KEY: str
    AZURE_SEARCH_INDEX_NAME: str = "enterprise-knowledge-base"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
