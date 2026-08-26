import sys
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError

from app.config import settings

safe_password = urllib.parse.quote_plus(settings.DB_PASSWORD)


SQLALCHEMY_DATABASE_URL = (
    f"postgresql+psycopg://{settings.DB_USER}:{safe_password}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"connect_timeout": 5}, 
        echo=False
    )
    if "pytest" not in sys.modules and "generate_readme" not in sys.argv[0]:
        with engine.connect() as connection:
            print("🔌 Database connection verified successfully!")
except OperationalError as e:
    print(f"\n❌ CRITICAL: Failed to connect to the database!\nDetails: {e}")
    sys.exit(1)
        
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
