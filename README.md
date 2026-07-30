## ⚠️ Caution & Known Limitations

> [!WARNING]
> This project is currently in its initial development phase. Please note the following lack of robust error prevention mechanisms:


# 💰 Expense Tracker API (Enterprise ORM Edition)

A professional, production-ready RESTful API for tracking personal expenses, built with **FastAPI** and **SQLAlchemy ORM**, backed by a relational **PostgreSQL** database. 

This project features a decoupled, scalable architecture separating API routers, database configurations, business logic (CRUD), and data validation schemas.

## 🚀 Features

- **Object-Relational Mapping (ORM)**: Built using native **SQLAlchemy** classes and relationships instead of legacy raw SQL string statements.
- **Dependency Injection**: Safe session tracking using FastAPI's `Depends` manager to completely prevent database connection memory resource leaks.
- **Smart Analytics Engine**: Aggregates complex database tracking math metrics (`COUNT`, `SUM`, `AVG`, `MAX`) dynamically using database functions.
- **Resilient Search Subsystem**: Integrates full case-insensitive partial keyword scanning (`ILIKE`) crossing database description strings and category names natively.
- **Automatic Structural Migrations**: Auto-evaluates model configurations and constructs tables natively into your active database instance upon startup.

## 🛠️ Prerequisites

Before launching the server, ensure your local environment contains:
- Python 3.10+
- Active PostgreSQL Database Socket Server

## 📦 Installation & Setup

1. **Navigate** to your source destination directory:
   ```bash
   cd path/to/expense-api
   ```

2. **Install all required dependencies** compiled inside the system manifest:
   ```bash
   pip install -r requirements.txt
   ```

3. **Database Configuration**:
   Open `database.py` and modify the dictionary properties inside the `create_engine` parameters block to align with your personal environment credentials:
   ```python
   engine = create_engine(
       "postgresql+psycopg://",
       connect_args={
           "host": "127.0.0.1",
           "port": "5432",
           "dbname": "expense_tracker",
           "user": "postgres",
           "password": "YOUR_ACTUAL_PASSWORD"
       },
       echo=True # Prints generated SQL commands directly to the terminal for easy debugging
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
```text
expense-api/
│
├── database.py     # Database engine, connection configurations, and session local factories
├── models.py       # Core SQLAlchemy relational database table blueprints
├── schemas.py      # Pydantic network data validation and parsing schemas
├── crud.py         # Business operations logic utilizing pure Python ORM interactions
├── main.py         # FastAPI application initializing endpoints and web routing controls
├── requirements.txt# Manifest of system dependencies and external library pins
└── README.md       # Comprehensive system documentation


## 🛣️ API Endpoints Summary

### 1. Expenses Core
- **`POST /expense`** - Adds a new expense row entry. Generates an `HTTP 201 Created` status code.
- **`GET /expense`** - Fetches all recorded expenses mapped to their relation strings.
- **`DELETE /expense`** - Removes a specific expense item evaluating matching parameter contexts safely.

### 2. Advanced Search & Filtering
- **`PUT /expenses/{id}`** - Updates an existing record targeted via its primary key URL path variable.
- **`GET /expenses/category/{category}`** - Returns a subset of expenses filtering explicitly under one singular category string case-insensitively.
- **`GET /expenses/search?keyword=coffee`** - Scans the database and handles partial matches across descriptions or categories seamlessly.

### 3. Analytics Matrix
- **`GET /expenses/stats`** - Computes high-level overview metrics tracking entry counts, totals, averages, and your highest singular recorded asset description.


> [!IMPORTANT]
> Because this system employs a strict relational Foreign Key block design, **you cannot save an expense under a category that does not exist inside your database**. 
> Before creating your first expense entry via the API, execute this seed statement inside your database terminal/tool (e.g., pgAdmin) to build a matching relational record:
> ```sql
> INSERT INTO categories (name) VALUES ('Shopping'), ('Food');
> 