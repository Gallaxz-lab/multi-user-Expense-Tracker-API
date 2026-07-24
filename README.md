## ⚠️ Caution & Known Limitations

> [!WARNING]
> This project is currently in its initial development phase. Please note the following lack of robust error prevention mechanisms:

- **No Advanced Error Handling**: The system does not yet catch database connection dropouts or unexpected crashes inside Python smoothly.
- **Strict Data Validation Missing**: There is no automatic correction or validation checking for typos, extra whitespaces, or uppercase/lowercase mismatches (e.g., entering "food" vs "Food" might cause category lookup failures).
- **Missing Dynamic Category Insertion**: If you add an expense with a category that does not already exist in the database, the API will simply throw a `400 Bad Request` instead of creating the category automatically.
- **Explicit Type Enforcement Required**: Ensure that the data payload perfectly matches the type expectations to prevent runtime exceptions.


# 💰 Expense Tracker API

A lightweight and robust RESTful API for tracking personal expenses, built with **FastAPI** and **PostgreSQL**. The system features relational database storage with automatic category mapping.

## 🚀 Features

- **Relational Database**: Uses PostgreSQL with an `INNER JOIN` structure between expenses and categories.
- **Auto-Validation**: Automatic request validation using Pydantic models.
- **Interactive Docs**: Built-in Swagger UI for quick API testing.
- **Clean Architecture**: Decoupled codebase separating database queries (`database.py`) from API endpoints (`main.py`).

## 📦 Installation & Setup

1. **Clone or navigate** to your project directory:
   ```bash
   cd path/to/python-postgres-expense
   ```

2. **Install required dependencies**:
   ```bash
   pip install fastapi uvicorn psycopg
   ```

3. **Database Configuration**:
   Open `database.py` and update your PostgreSQL connection parameters in the `get_db_connection()` function:
   ```python
   def get_db_connection():
       return psycopg.connect(
           host="127.0.0.1",
           port="5432",
           dbname="expense_tracker",
           user="postgres",
           password="YOUR_PASSWORD"
       )
   ```

## 🏃 Running the Application
Start the FastAPI server using Uvicorn:
```bash
uvicorn main:app --reload


## 📑 API Documentation & Testing
FastAPI automatically generates interactive documentation. Once the server is running, open your browser and navigate to:

👉 **[http://127.0.0] or (http://localhost:8000/docs#/)** (Swagger UI)


## 📂 Project Structure
python-postgres-expense/
├── database.py   # Handles database connections, tables initialization, and SQL queries (CRUD)
├── main.py       # Configures FastAPI app, Pydantic schemas, and web routing (Endpoints)
└── README.md     # Project documentation