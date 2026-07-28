from database import get_db_connection
from datetime import date

def init_db():
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""                       
                CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
                category_id INTEGER REFERENCES categories(id),
                description TEXT NOT NULL, amount REAL NOT NULL,
                date DATE NOT NULL DEFAULT CURRENT_DATE
                );
            """)
        conn.commit()

def add_expense(category: str, description: str, amount: float, expense_date: date):
    cleaned_category = category.strip()
    cleaned_description = description.strip()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name ILIKE %s;", (cleaned_category,))
            result = cur.fetchone()
            if result is None:
                return {"success": False, "massage": f"Category '{cleaned_category}' does not exist!"}
            category_id = result[0] 
            cur.execute("INSERT INTO expenses (category_id, description, amount, date) VALUES (%s, %s, %s, %s);",(category_id, cleaned_description, amount, expense_date),)
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
    cleaned_category = category.strip()
    cleaned_description = description.strip()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name ILIKE %s;", (cleaned_category,))
            result = cur.fetchone()
            if result is None:
                return {"success": False, "message": f"Category '{cleaned_category}' does not exist!"}   
            category_id = result[0]
            cur.execute("""
                UPDATE expenses 
                SET category_id = %s, description = %s, amount = %s, date = %s
                WHERE id = %s;
            """, (category_id, cleaned_description, amount, expense_date, expense_id))
            if cur.rowcount == 0:
                return {"success": False, "message": f"Expense ID {expense_id} not found!"}   
            conn.commit()
            return {"success": True, "message": f"Expense ID {expense_id} updated successfully!"}
        
        
                    
def delete_expense(category: str, description: str, amount: float):
    cleaned_category = category.strip()
    cleaned_description = description.strip()
    show_expenses()
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name ILIKE %s;", (cleaned_category,))
            result = cur.fetchone()
            if result is None:
                return {"success": False, "massage": f"Category '{cleaned_category}' does not exist!"}
            category_id = result[0] 
            cur.execute("DELETE FROM expenses WHERE category_id = %s AND description = %s AND amount = %s;", (category_id, cleaned_description, amount))
            conn.commit()
            return {"success": True, "massage": "deleted successfully!"}
        
        
        
def get_expense_category(category: str):
    cleaned_category = category.strip()
    with get_db_connection()as conn:
        with conn.cursor()as cur:
            cur.execute("SELECT id FROM categories WHERE name ILIKE %s;", (cleaned_category,))
            result = cur.fetchone()
            if result is None:
                return {"status" : "not_found", "massage": f"Category '{cleaned_category}' does not exist!"}
            cur.execute("""
                        SELECT expenses.id, categories.name, expenses.description, expenses.amount, expenses.date 
                FROM expenses 
                INNER JOIN categories ON expenses.category_id = categories.id
                WHERE categories.name ILIKE %s
            """, (cleaned_category,))
            rows = cur.fetchall()
            exp_list = []
            for row in rows:
                exp_list.append({
                    "id": row[0],
                    "category": row[1],
                    "description": row[2],
                    "amount": row[3],
                    "date": str(row[4])
                })
            return {"status": "completed", "data": exp_list}
            
def get_expense_stats():
    with get_db_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("SELECT COUNT(*), SUM(amount), AVG(amount) FROM expenses;")
            stats_result = cur.fetchone()
            if stats_result is None or stats_result[0] == 0:
                return {
                    "status": "completed",
                    "data": {
                        "total_expenses": 0,
                        "total_amount": 0.0,
                        "average_amount": 0.0,
                        "highest_expense": None
                    }
                }
            total_expenses = stats_result[0]
            total_amount = float(stats_result[1]) if stats_result[1] else 0.0
            average_amount = round(float(stats_result[2]), 2) if stats_result[2] else 0.0
            cur.execute("""
                SELECT description, amount 
                FROM expenses 
                ORDER BY amount DESC 
                LIMIT 1;
            """)
            highest_result = cur.fetchone()
            highest_expense = None
            if highest_result:
                highest_expense = {
                    "description": highest_result[0],
                    "amount": float(highest_result[1])
                }
            return {
                "status": "completed",
                "data": {
                    "total_expenses": total_expenses,
                    "total_amount": total_amount,
                    "average_amount": average_amount,
                    "highest_expense": highest_expense
                }
            }