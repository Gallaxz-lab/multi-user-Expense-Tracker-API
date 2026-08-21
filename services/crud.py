from sqlalchemy import func, or_
from sqlalchemy.orm import Session
from datetime import date
import models.expense as models

def _get_category_or_create(db: Session, category_name: str, owner_id: int):
    cat = db.query(models.Category).filter(
        models.Category.name.ilike(category_name.strip()),
        models.Category.owner_id == owner_id
    ).first()
    if not cat:
        cat = models.Category(name=category_name.strip(), owner_id=owner_id)
        db.add(cat)
        db.commit()
        db.refresh(cat)
    return cat

def add_expense(db: Session, category: str, description: str, amount: float, expense_date: date, owner_id: int):
    category_row = _get_category_or_create(db, category, owner_id)
    new_expense = models.Expense(
        category_id=category_row.id,
        description=description.strip(),
        amount=amount,
        date=expense_date,
        owner_id=owner_id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return {"success": True, "message": "Expense added successfully!", "data": new_expense}

def show_expenses(db: Session, owner_id: int, limit: int, offset: int, sort: str, order: str):
    query = db.query(models.Expense).filter(models.Expense.owner_id == owner_id)
    sort_attr = models.Expense.amount if sort == "amount" else models.Expense.date
    query = query.order_by(sort_attr.desc() if order == "desc" else sort_attr.asc())
    return query.offset(offset).limit(limit).all()

def delete_expense_by_match(db: Session, category: str, description: str, amount: float, owner_id: int):
    cat = db.query(models.Category).filter(models.Category.name.ilike(category.strip()), models.Category.owner_id == owner_id).first()
    if not cat:
        return {"success": False, "message": f"Category '{category.strip()}' does not exist!"}
    target = db.query(models.Expense).filter(
        models.Expense.category_id == cat.id,
        models.Expense.description.ilike(description.strip()),
        models.Expense.amount == amount,
        models.Expense.owner_id == owner_id
    ).first()
    if not target:
        return {"success": False, "message": "Expense record not found!"}
    db.delete(target)
    db.commit()
    return {"success": True, "message": "Deleted successfully!"}

def update_expense_by_id(db: Session, expense_id: int, category: str, description: str, amount: float, expense_date: date, owner_id: int):
    expense_row = db.query(models.Expense).filter(models.Expense.id == expense_id, models.Expense.owner_id == owner_id).first()
    if not expense_row:
        return {"status": "not_found", "message": f"Expense ID {expense_id} not found!"}
    category_row = _get_category_or_create(db, category, owner_id)
    expense_row.category_id = category_row.id
    expense_row.description = description.strip()
    expense_row.amount = amount
    expense_row.date = expense_date
    db.commit()
    db.refresh(expense_row)
    return {"status": "completed", "message": f"Expense ID {expense_id} updated successfully!", "data": expense_row}

def get_expenses_by_category(db: Session, category_name: str, owner_id: int):
    cat = db.query(models.Category).filter(models.Category.name.ilike(category_name.strip()), models.Category.owner_id == owner_id).first()
    if not cat:
        return {"status": "not_found", "message": f"Category '{category_name.strip()}' does not exist!"}
    expenses = db.query(models.Expense).filter(models.Expense.category_id == cat.id, models.Expense.owner_id == owner_id).all()
    return {"status": "completed", "data": expenses}

def get_expense_stats(db: Session, owner_id: int):
    stats = db.query(
        func.count(models.Expense.id),
        func.sum(models.Expense.amount),
        func.avg(models.Expense.amount)
    ).filter(models.Expense.owner_id == owner_id).first()
    if not stats or stats[0] == 0:
        return {"status": "completed", "data": {"total_expenses": 0, "total_amount": 0.0, "average_amount": 0.0, "highest_expense": None}}
    highest = db.query(models.Expense).filter(models.Expense.owner_id == owner_id).order_by(models.Expense.amount.desc()).first()
    highest_expense = {"description": highest.description, "amount": float(highest.amount)} if highest else None
    return {
        "status": "completed",
        "data": {
            "total_expenses": stats[0],
            "total_amount": float(stats[1]) if stats[1] else 0.0,
            "average_amount": round(float(stats[2]), 2) if stats[2] else 0.0,
            "highest_expense": highest_expense
        }
    }

def search_expenses(db: Session, keyword: str, owner_id: int):
    cleaned = f"%{keyword.strip()}%"  
    return db.query(models.Expense).join(models.Category).filter(
        models.Expense.owner_id == owner_id,
        or_(models.Expense.description.ilike(cleaned), models.Category.name.ilike(cleaned))
    ).all()
