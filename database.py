import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from config import settings

try:
    engine = create_engine(
        "postgresql+psycopg://", 
        connect_args={
            "host": settings.DBDB_HOST,
            "port": settings.DB_PORT,
            "dbname": settings.DB_NAME,
            "user": settings.DB_USER,
            "password": settings.DB_PASSWORD,
            "connect_timeout" :5   
        },
        echo=False
    )
    with engine.connect() as connection:
        print("🔌 Database connection verified successfully!")
        
except OperationalError as e:
    print("\n❌ CRITICAL: Failed to connect to the PostgreSQL database server!")
    print(f"Details: {e}")
    print("Please verify that your PostgreSQL service is running and that your .env details are correct.\n")
    sys.exit(1)
        
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
"""
def get_db_connection():
    return psycopg.connect(
        host="127.0.0.1",
        port="5432",
        dbname="expense_tracker",
        user="postgres",
        password="@Won083104"
        )

DATABASE_URL = "postgresql+psycopg://postgres:@Won083104@127.0.0.1:5432/expense_tracker"

engine = create_engine(DATABASE_URL, echo=True)

Sessionlocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base = declarative_base()

def get_db():
    db = Sessionlocal()
    try:
        yield db
    finally:
        db.close()
"""