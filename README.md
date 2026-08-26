# 💰 Multi-User Expense Tracker API

A production-ready asynchronous REST API framework engineered with FastAPI, PostgreSQL, SQLAlchemy, and Docker.

---

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

## 🚀 Live API Endpoint Inventory

The system automatically inventory checks and tracks the following live route endpoints:

| Method | Endpoint | Description | Tags |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | No description provided. | System Infrastructure |

---

## 🐳 Containerized Quick Start

1. Ensure you have configured your environment credentials inside your local `.env` file.
2. Build and initialize your container network ecosystem using Docker Compose:
   ```bash
   docker compose -f compose.yaml up --build
   ```
3. Once running, access your automated API documentation sandbox directly at: **http://localhost:8000/docs**