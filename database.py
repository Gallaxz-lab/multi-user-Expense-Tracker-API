from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


engine = create_engine(
    "postgresql+psycopg://",  # Keep the prefix blank
    connect_args={
        "host": "127.0.0.1",
        "port": "5432",
        "dbname": "expense_tracker",
        "user": "postgres",
        "password": "@Won083104"  
    },
    echo=True
)

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