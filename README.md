# 💰 Multi-User Expense Tracker API

A production-ready, highly optimized asynchronous REST API engine engineered with **FastAPI**, **PostgreSQL**, **SQLAlchemy ORM**, and **Docker**. 

This system features complete cryptographic user isolation (JWT architecture), containerized service orchestrations, and automated deployment checks.

## 🔗 Live Production Access
* **Interactive API Playground:** [Swagger UI Docs Docs](https://onrender.com)
* **Live System Health Metrics Check:** [Operational Infrastructure Ping](https://multi-user-expense-tracker-api.onrender.com)


## ⚡ Key Architectural Highlights
* 🔑 **Cryptographic Security:** Secure token-based user authentication using `PyJWT` and `passlib` (bcrypt).
* 🗄️ **Relational Database Design:** Complete data normalization separating `Users`, `Categories`, and `Expenses` with active cascading constraints.
* 📈 **Advanced Query Metrics:** Multi-parameter route sorting, pagination limiting, search parameters processing, and regex keyword mapping.
* 📦 **Container Architecture:** Fully isolated local and cloud development environments using multi-stage Docker builds.
* 🤖 **Continuous Integration (CI):** Fully automated automated checking pipeline using GitHub Actions to evaluate module paths and dependencies.



## 🛠️ Automated System Architecture Layout

Below is the dynamically mapped blueprint of this codebase structure:

```text
└── multi-user-Expense-Tracker-API/
    ├── .dockerignore
    ├── .env
    ├── .env.example
    ├── .gitignore
    ├── Dockerfile
    ├── compose.debug.yaml
    ├── compose.yaml
    ├── requirements.txt
    └── .github/
        ├── ci.yml
        └── workflows/
    └── app/
        ├── config.py
        ├── main.py
        └── database/
            ├── connection.py
        └── models/
            ├── expense.py
            ├── user.py
        └── routers/
            ├── auth.py
            ├── expenses.py
        └── schemas/
            ├── auth.py
            ├── expense.py
        └── services/
            ├── crud.py
            ├── security.py
```

---

### 🚀 Live API Endpoint Inventory

The system dynamically tracks and serves the following verified live endpoints:

### 🔐 Authentication System

| Method | Endpoint | Description | Tags |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Registers a new user account with hashed credentials. | Authentication |
| `POST` | `/auth/login` | Validates user signatures and issues secure JWT tokens. | Authentication |

### 📈 Expense Infrastructure

| Method | Endpoint | Description | Tags |
| :--- | :--- | :--- | :--- |
| `POST` | `/expenses` | Records a new user transaction linked to an automated category. | Expenses |
| `GET` | `/expenses` | Retrieves user records with active pagination and sorting parameters. | Expenses |
| `PUT` | `/expenses/{id}` | Updates existing operational data objects by explicit record ID matching. | Expenses |
| `DELETE` | `/expenses` | Deletes specific records safely using data-matching metrics. | Expenses |
| `GET` | `/expenses/search` | Parses your database records using regex/keyword matching filters. | Expenses |
| `GET` | `/expenses/stats` | Compiles comprehensive financial summaries and category totals. | Expenses |
| `GET` | `/expenses/category/{cat}`| Tracks financial logs isolated strictly by a specified category tier. | Expenses |

### 🩺 System Diagnostics

| Method | Endpoint | Description | Tags |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Verifies live cloud runtime storage and database availability. | System Infrastructure |

---

## 🐳 Containerized Quick Start (Local Development)

### 1. Configure Local Environment Variables
Create a local `.env` file at your root directory using the layout provided in `.env.example`:
```env
DB_USER=postgres
DB_PASSWORD=your_secure_password
DB_HOST=db
DB_PORT=5432
DB_NAME=expense_tracker
SECRET_KEY=your_cryptographic_signing_key_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
PORT=8000
```

### 2. Boot up the Container Stack
Launch the isolated database network and backend engine with a single orchestrated command:
```bash
docker compose up --build
```

### 3. Access Locally
* Open the **Interactive API Docs:** `http://localhost:8000/docs`
* Check **Database Connectivity Status:** `http://localhost:8000/health`