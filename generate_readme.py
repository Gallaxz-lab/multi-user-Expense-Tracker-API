import os

def generate_project_tree(startpath):
    """Dynamically builds a clean visual folder layout filtering out junk."""
    tree = []
    exclude_dirs = {'.git', '__pycache__', 'venv', '.pytest_cache', '.vscode', 'postgres_data'}
    exclude_files = {'api_schema.json', 'generate_readme.py'}
    
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * level
        folder_name = os.path.basename(root)
        
        if folder_name and folder_name not in exclude_dirs:
            tree.append(f"{indent}└── {folder_name}/")
            
        sub_indent = ' ' * 4 * (level + 1)
        for f in sorted(files):
            if f not in exclude_files and not f.endswith('.pyc') and not f.endswith('.env'):
                tree.append(f"{sub_indent}├── {f}")
    return "\n".join(tree)

def build_markdown_readme():
    print("⏳ Rewriting portfolio documentation assets...")
    project_tree = generate_project_tree(os.getcwd())
    
    readme_template = f"""# 💰 Multi-User Expense Tracker & Intelligent AI Financial Agent

A production-ready, highly optimized asynchronous REST API engine engineered with **FastAPI**, **PostgreSQL**, **SQLAlchemy ORM**, and **Google Gemini Flash**. 

This system features complete cryptographic user data isolation (JWT architecture), containerized service orchestrations, real-time natural language query parsing, and automated deployment checks.

## 🔗 Production Quick Links
* 🚀 **Interactive API Playground:** [Live Swagger UI Docs](https://multi-user-expense-tracker-api.odnrender.com/docs)
* 🩺 **System Infrastructure Status:** [Live Health Check Endpoint](https://multi-user-expense-tracker-api.onrender.com/health)

---

## ⚡ Key Architectural Highlights
* 🧠 **Gemini AI Integration:** Features a natural language endpoint processing multi-modal/text queries to automatically parse categories, amounts, and dates from unstructured casual strings.
* 🔑 **Cryptographic Security:** Secure token-based user authentication using `PyJWT` and `passlib` (bcrypt).
* 🗄️ **Relational Database Design:** Complete data normalization separating `Users`, `Categories`, and `Expenses` with active cascading constraints.
* 📈 **Advanced Query Metrics:** Multi-parameter route sorting, pagination limiting, search parameters processing, and regex keyword mapping.
* 📦 **Container Architecture:** Fully isolated local and cloud development environments using multi-stage Docker builds.
* 🤖 **Continuous Integration (CI):** Fully automated checking pipeline using GitHub Actions to evaluate module paths and dependencies.

---

## 🛠️ Automated System Architecture Layout

Below is the verified blueprint of this codebase structure:

```text
{project_tree}
```

---

## 🚀 Live API Endpoint Inventory

The system dynamically tracks and serves the following verified live endpoints:

### 🔐 Authentication System

| Method | Endpoint | Description | Tags |
| :--- | :--- | :--- | :--- |
| `POST` | `/auth/register` | Registers a new user account with hashed credentials. | Authentication |
| `POST` | `/auth/login` | Validates user signatures and issues secure JWT tokens. | Authentication |

### 📈 Expense Infrastructure & AI Agents

| Method | Endpoint | Description | Tags |
| :--- | :--- | :--- | :--- |
| `POST` | `/expenses/ai-add` | 🤖 **AI Agent:** Processes natural text strings, extracts parameters via Gemini, and saves. | Expenses |
| `POST` | `/expenses` | Records a new standard user transaction linked to an automated category. | Expenses |
| `GET` | `/expenses` | Retrieves user records with active pagination and sorting parameters. | Expenses |
| `PUT` | `/expenses/{{id}}` | Updates existing operational data objects by explicit record ID matching. | Expenses |
| `DELETE` | `/expenses` | Deletes specific records safely using data-matching metrics. | Expenses |
| `GET` | `/expenses/search` | Parses your database records using regex/keyword matching filters. | Expenses |
| `GET` | `/expenses/stats` | Compiles comprehensive financial summaries and category totals. | Expenses |
| `GET` | `/expenses/category/{{cat}}`| Tracks financial logs isolated strictly by a specified category tier. | Expenses |

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
GEMINI_API_KEY=your_google_ai_studio_api_key
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
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_template.strip())
        
    print("✅ Success! README.md has been cleanly rebuilt and formatted for interviewers.")

if __name__ == "__main__":
    build_markdown_readme()
