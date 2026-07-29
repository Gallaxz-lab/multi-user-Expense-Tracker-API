from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from datetime import date
from database import engine, Base
import models

def init_db():
    Base.metadata.create_all(bind=engine)
    
def add_expense(db: Session, category: str, description: str, amount: float, expense_date: date):
    cleaned_category = category.strip()
    cleaned_description = description.strip()
    
    category_row = db.query(models.Category).filter(models.Category.name.ilike(cleaned_category)).first()
    
    if category_row is None:
        return {"success": False, "message": f"Category {cleaned_category} does not exist!"}
    
    new_expense = models.Expense(
        category_id=category_row.id,
        description=cleaned_description,
        amount=amount,
        date=expense_date
    )
    
    db.add(new_expense)
    db.commit()
    return {"success": True, "message": "Expense added successfully!"}
                
    
def show_expenses(db: Session):
    expenses = db.query(models.Expense).all()
    exp_list = []
    for exp in expenses:
        exp_list.append({
            "id": exp.id,
            "category": exp.category_rel.name,
            "description": exp.description,
            "amount": exp.amount,
            "date": str(exp.date)
        })
    return exp_list


def delete_expense(db: Session, category: str, description: str, amount: float):
    cleaned_category = category.strip()
    cleaned_description = description.strip()

    category_row = db.query(models.Category).filter(models.Category.name.ilike(cleaned_category)).first()
    if category_row is None:
        return {"success": False, "message": f"Category '{cleaned_category}' does not exist!"}

    target_expense = db.query(models.Expense).filter(
        models.Expense.category_id == category_row.id,
        models.Expense.description.ilike(cleaned_description),
        models.Expense.amount == amount
    ).first()

    if target_expense is None:
        return {"success": False, "message": "Expense record not found!"}

    db.delete(target_expense)
    db.commit()
    return {"success": True, "message": "Deleted successfully!"}

def update_expense_by_id(db: Session, expense_id: int, category: str, description: str, amount: float, expense_date: date):
    cleaned_category = category.strip()
    cleaned_description = description.strip()

    category_row = db.query(models.Category).filter(models.Category.name.ilike(cleaned_category)).first()
    if category_row is None:
        return {"status": "category_missing", "message": f"Category '{cleaned_category}' does not exist!"}

    expense_row = db.query(models.Expense).filter(models.Expense.id == expense_id).first()
    if expense_row is None:
        return {"status": "not_found", "message": f"Expense ID {expense_id} not found!"}


    expense_row.category_id = category_row.id
    expense_row.description = cleaned_description
    expense_row.amount = amount
    expense_row.date = expense_date

    db.commit()
    return {"status": "completed", "message": f"Expense ID {expense_id} updated successfully!"}

def get_expenses_by_category(db: Session, category_name: str):
    cleaned_category = category_name.strip()

    category_row = db.query(models.Category).filter(models.Category.name.ilike(cleaned_category)).first()
    if category_row is None:
        return {"status": "not_found", "message": f"Category '{cleaned_category}' does not exist!"}

    expenses = db.query(models.Expense).filter(models.Expense.category_id == category_row.id).all()
    
    exp_list = []
    for exp in expenses:
        exp_list.append({
            "id": exp.id,
            "category": category_row.name,
            "description": exp.description,
            "amount": exp.amount,
            "date": str(exp.date)
        })
    return {"status": "completed", "data": exp_list}

def get_expense_stats(db: Session):
    stats = db.query(
        func.count(models.Expense.id),
        func.sum(models.Expense.amount),
        func.avg(models.Expense.amount)
    ).first()

    if not stats or stats[0] == 0:
        return {
            "status": "completed",
            "data": {"total_expenses": 0, "total_amount": 0.0, "average_amount": 0.0, "highest_expense": None}
        }

    highest = db.query(models.Expense).order_by(models.Expense.amount.desc()).first()
    highest_expense = None
    if highest:
        highest_expense = {
            "description": highest.description,
            "amount": float(highest.amount)
        }

    return {
        "status": "completed",
        "data": {
            "total_expenses": stats[0],
            "total_amount": float(stats[1]) if stats[1] else 0.0,
            "average_amount": round(float(stats[2]), 2) if stats[2] else 0.0,
            "highest_expense": highest_expense
        }
    }
    
    


def search_expenses(db: Session, keyword: str):
    cleaned_keyword = f"%{keyword.strip()}%"  

    expenses = db.query(models.Expense).join(models.Category).filter(
        or_(
            models.Expense.description.ilike(cleaned_keyword), 
            models.Category.name.ilike(cleaned_keyword)      
        )
    ).all()

    exp_list = []
    for exp in expenses:
        exp_list.append({
            "id": exp.id,
            "category": exp.category_rel.name,
            "description": exp.description,
            "amount": exp.amount,
            "date": str(exp.date)
        })
    return exp_list


"""
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
            cur.execute(/*
                UPDATE expenses 
                SET category_id = %s, description = %s, amount = %s, date = %s
                WHERE id = %s;*/, (category_id, cleaned_description, amount, expense_date, expense_id))
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
            cur.execute(*/
                        SELECT expenses.id, categories.name, expenses.description, expenses.amount, expenses.date 
                FROM expenses 
                INNER JOIN categories ON expenses.category_id = categories.id
                WHERE categories.name ILIKE %s
            */, (cleaned_category,))
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
            cur.execute(*/SELECT description, amount FROM expenses ORDER BY amount DESC LIMIT 1;*/)
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
            
"""