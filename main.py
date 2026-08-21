import uvicorn
from fastapi import FastAPI
from database.connection import Base, engine
from routers import auth, expenses

# Automatically execute operational table blueprints inside PostgreSQL
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Expense Tracker Advanced API")

# Bind structural sub-routers
app.include_router(auth.router)
app.include_router(expenses.router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
