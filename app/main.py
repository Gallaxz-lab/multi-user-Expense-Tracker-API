import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Internal domain namespace alignment imports
from app.config import settings
from app.routers import auth, expenses

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

# Register Sub-Domain Architecture Router Modules
app.include_router(auth.router)
app.include_router(expenses.router)
