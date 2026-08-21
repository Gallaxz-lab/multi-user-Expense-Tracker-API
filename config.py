import os
from dotenv import load_dotenv

load_dotenv()

class Setting:
    # Fixed the typo here from DBDB_HOST to DB_HOST
    DB_HOST: str = os.getenv("DB_HOST", "127.0.0.1")
    DB_PORT: str = os.getenv("DB_PORT", "5432")
    DB_NAME: str = os.getenv("DB_NAME", "expense_tracker")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "b3dfa72c1106e2a2202685cb5b26df700f135abc")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# This is what database/connection.py is looking for when it calls "settings"
settings = Setting()
