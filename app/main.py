import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Internal domain namespace alignment imports
from app.config import settings
from app.routers import auth, expenses, search

from app.database.connection import engine, Base
from app.models.user import User
from app.models.expense import Expense, Category

Base.metadata.create_all(bind=engine)

# --- Basic Stream Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()] # Broadcasts straight to terminal & docker app logs
)
logger = logging.getLogger("expense_tracker")

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    docs_url="/docs"
)

# --- Basic CORS Middleware Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"], 
    allow_credentials=True,
    allow_methods=["*"], 
    allow_headers=["*"], 
)

# --- Universal Exception/Error Handling Catch-All ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception intercepted on route {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please review runtime tracking logs."}
    )

# --- System Isolation Health Check End-Route ---
@app.get("/health", status_code=status.HTTP_200_OK, tags=["System Infrastructure"])
async def health_check():
    logger.info("Health check ping registered by runtime agent")
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }
    
# 📂 Open app/main.py and replace your startup event block:

from sqlalchemy import text # ✅ Ensure you import text at the top of main.py if not present

@app.on_event("startup")
def configure_database_tables_on_boot():
    print("🛢️ Connecting to database cluster engine and verifying table schemas...")
    
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as connection:
        with connection.begin():
            print("🔧 Checking for missing enterprise user tracking columns inside PostgreSQL...")
            
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR DEFAULT 'User';"
            ))
            connection.execute(text(
                "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;"
            ))
            
    print("✅ Live PostgreSQL database tables successfully synchronized and upgraded!")


# Register Sub-Domain Architecture Router Modules
app.include_router(auth.router)
app.include_router(expenses.router)
app.include_router(search.router)
