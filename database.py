import psycopg
from tabulate import tabulate

def add_expense():
    print("\n--- Add the Expense ---")
    category = input("Cetagory (Ex. Food, Shopping): ")
    Description = input("Description (Ex. chicken, New t-shirt): ")
    try:
        amount = float(input("Please input the amount (Bath): "))
    except ValueError:
        print("❌ Please type the amount!! (number only!)")
        return
    with psycopg.connect(host="127.0.0.1", port="5432",dbname="expense_tracker",user="postgres",password="@Won083104") as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM categories WHERE name = %s;", (category,))
                result = cur.fetchone()
                if result is None:
                    print(f"Error: Category '{category}' does not exist! Please create it first.")
                else:
                    category_id = result[0] 
                    cur.execute("INSERT INTO expenses (category_id, description, amount) VALUES (%s, %s, %s);",(category_id, Description, amount),)
                    conn.commit()
                    print("Expense added successfully!")
                
    
def show_expenses():
    with psycopg.connect(host="127.0.0.1", port="5432",dbname="expense_tracker",user="postgres",password="@Won083104") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT expenses.id, categories.name, expenses.description, expenses.amount FROM expenses INNER JOIN categories ON expenses.category_id = categories.id")
            rows = cur.fetchall()
            headers = ["ID", "Category", "Description", "Amount"]
            print(tabulate(rows, headers=headers, tablefmt="plain"))
                    
def delete_expense():
    print("\n---- delet the expense----")
    show_expenses()
    category = input("Cetagory (Ex. Food, Shopping): ")
    Description = input("Description (Ex. chicken, New t-shirt): ")
    try:
        amount = float(input("Please input the amount (Bath): "))
    except ValueError:
        print("❌ Please type the amount!! (number only!)")
        return
    with psycopg.connect(host="127.0.0.1", port="5432",dbname="expense_tracker",user="postgres",password="@Won083104") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM categories WHERE name = %s;", (category,))
            result = cur.fetchone()
            if result is None:
                print(f"Error: Category '{category}' does not exist! Please create it first.")
            else:
                category_id = result[0] 
                cur.execute("DELETE FROM expenses WHERE category_id = %s AND description = %s AND amount = %s;", (category_id, Description, amount))
                conn.commit()
                print("deleted successfully!")