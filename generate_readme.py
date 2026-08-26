import os
from app.main import app
from fastapi.routing import APIRoute

def generate_project_tree(startpath):
    """Dynamically builds a clean visual folder layout filtering out junk."""
    tree = []
    exclude_dirs = {'.git', '__pycache__', 'venv', '.pytest_cache', '.vscode'}
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
            if f not in exclude_files and not f.endswith('.pyc'):
                tree.append(f"{sub_indent}├── {f}")
    return "\n".join(tree)

def extract_api_endpoints():
    """Reads your live FastAPI instance to inventory all operational routes."""
    routes_markdown = []
    routes_markdown.append("| Method | Endpoint | Description | Tags |")
    routes_markdown.append("| :--- | :--- | :--- | :--- |")
    
    # 1. Filter out structural wrappers and only process actionable routes
    api_routes = [r for r in app.routes if isinstance(r, APIRoute)]
    
    # 2. Sort by path cleanly now that we have uniform objects
    for route in sorted(api_routes, key=lambda x: x.path):
        # Ignore default FastAPI metadata documentation endpoints
        if route.path in ["/docs", "/redoc", "/openapi.json"]:
            continue
            
        methods = ", ".join(route.methods)
        summary = route.summary if route.summary else "No description provided."
        tags = ", ".join(route.tags) if route.tags else "None"
        
        routes_markdown.append(f"| `{methods}` | `{route.path}` | {summary} | {tags} |")
        
    return "\n".join(routes_markdown)

def build_markdown_readme():
    """Assembles all dynamic sections together into a beautiful README.md file."""
    print("⏳ Analyzing your project structure and route metrics...")
    
    project_tree = generate_project_tree(os.getcwd())
    api_endpoints_table = extract_api_endpoints()
    
    readme_template = f"""# 💰 Multi-User Expense Tracker API

A production-ready asynchronous REST API framework engineered with FastAPI, PostgreSQL, SQLAlchemy, and Docker.

---

## 🛠️ Automated System Architecture Layout

Below is the dynamically mapped blueprint of this codebase structure:

```text
{project_tree}
```

---

## 🚀 Live API Endpoint Inventory

The system automatically inventory checks and tracks the following live route endpoints:

{api_endpoints_table}

---

## 🐳 Containerized Quick Start

1. Ensure you have configured your environment credentials inside your local `.env` file.
2. Build and initialize your container network ecosystem using Docker Compose:
   ```bash
   docker compose -f compose.ymal up --build
   ```
3. Once running, access your automated API documentation sandbox directly at: **http://localhost:8000/docs**
"""

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_template.strip())
        
    print("✅ Success! README.md has been automatically regenerated and aligned with your code.")

if __name__ == "__main__":
    build_markdown_readme()
