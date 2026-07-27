import psycopg
from datetime import date


def get_db_connection():
    return psycopg.connect(host="127.0.0.1", port="5432",dbname="expense_tracker",user="postgres",password="@Won083104")

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS expenses (id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY, category_id INTEGER REFERENCES categories(id), description TEXT NOT NULL, amount REAL NOT NULL, date DATE NOT NULL DEFAULT CURRENT_DATE);")
        conn.commit()

def add_expense(category: str, description: str, amount: float, expense_date: date):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name = %s;", (category,))
            result = cur.fetchone()
            if result is None:
                return {"success": False, "massage": f"Category '{category}' does not exist!"}
            category_id = result[0] 
            cur.execute("INSERT INTO expenses (category_id, description, amount, date) VALUES (%s, %s, %s, %s);",(category_id, description, amount, expense_date),)
            conn.commit()
            return{"success": True, "massage": "Expense added successfully!"}
                
    
def show_expenses():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT expenses.id, categories.name, expenses.description, expenses.amount, expenses.date FROM expenses INNER JOIN categories ON expenses.category_id = categories.id")
            rows = cur.fetchall()
            exp_list = []
            for row in rows:
                exp_list.append({
                    "id": row[0],
                    "category": row[1],
                    "description": row[2],
                    "amount":row[3],
                    "date": str(row[4])
                })
            return exp_list
        
        
def update_expense(expense_id: int, category: str, description: str, amount: float, expense_date: date):
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name = %s;", (category,))
            result = cur.fetchone()
            if result is None:
                return {"success": False, "message": f"Category '{category}' does not exist!"}   
            category_id = result[0]
            cur.execute("""
                UPDATE expenses 
                SET category_id = %s, description = %s, amount = %s, date = %s
                WHERE id = %s;
            """, (category_id, description, amount, expense_date, expense_id))
            if cur.rowcount == 0:
                return {"success": False, "message": f"Expense ID {expense_id} not found!"}   
            conn.commit()
            return {"success": True, "message": f"Expense ID {expense_id} updated successfully!"}
                    
def delete_expense(category: str, description: str, amount: float):
    show_expenses()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name = %s;", (category,))
            result = cur.fetchone()
            if result is None:
                return {"success": False, "massage": f"Category '{category}' does not exist!"}
            category_id = result[0] 
            cur.execute("DELETE FROM expenses WHERE category_id = %s AND description = %s AND amount = %s;", (category_id, description, amount))
            conn.commit()
            return {"success": True, "massage": "deleted successfully!"}