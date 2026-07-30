import crud
import schemas
import uvicorn
from fastapi import FastAPI, HTTPException, status, Depends
from database import get_db
from sqlalchemy.orm import Session

app = FastAPI(title="Expense Tracker Advanced API")

crud.init_db()

@app.post("/expense", status_code=status.HTTP_201_CREATED)
def api_add_expense(payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    result = crud.add_expense(db, payload.category, payload.description, payload.amount, payload.date)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return result

@app.get("/expense", status_code=status.HTTP_200_OK)
def api_show_expense(db: Session = Depends(get_db)):
    return crud.show_expenses(db)

@app.delete("/expense", status_code=status.HTTP_200_OK)
def api_delete_expense(payload: schemas.ExpenseCreate, db: Session = Depends(get_db)):
    result = crud.delete_expense(db, payload.category, payload.description, payload.amount)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return result

@app.put("/expenses/{id}", status_code=status.HTTP_200_OK)
def api_update_expense(id: int, payload: schemas.ExpenseUpdate, db: Session = Depends(get_db)):
    result = crud.update_expense_by_id(db, id, payload.category, payload.description, payload.amount, payload.date)
    if result["status"] == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
    if result["status"] == "category_missing":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return {"message": result["message"]}

@app.get("/expenses/category/{category}", status_code=status.HTTP_200_OK)
def api_get_expenses_by_category(category: str, db: Session = Depends(get_db)):
    result = crud.get_expenses_by_category(db, category)
    if result["status"] == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
    return result["data"]

@app.get("/expenses/stats", status_code=status.HTTP_200_OK)
def api_get_expenses_stats(db: Session = Depends(get_db)):
    result = crud.get_expense_stats(db)
    return result["data"]


@app.get("/expenses/search", status_code=status.HTTP_200_OK)
def api_search_expenses(keyword: str, db: Session = Depends(get_db)):
    if not keyword.strip():
        return []
        
    return crud.search_expenses(db, keyword)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    
    
    
"""
@app.post("/expense", status_code=status.HTTP_201_CREATED)
def api_add_expense(payload: schemas.ExpenseCreate):
    result = crud.add_expense(payload.category, payload.description, payload.amount, payload.date)
    if not result["success"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return result

@app.put("/expense", status_code=status.HTTP_200_OK)
def api_put_expense(paylaod: schemas.ExpenseUpdate):
    result = crud.update_expense(paylaod.id, paylaod.category, paylaod.description, paylaod.amount, paylaod.date)
    if result["status"] == "not_found":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
    if result["status"] == "category_missing":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return {"message": result["message"]}

@app.get("/expense", status_code=status.HTTP_200_OK)
def api_show_expense():
    return crud.show_expenses()

@app.delete("/expense", status_code=status.HTTP_200_OK)
def api_delete_expense(paylaod: schemas.ExpenseCreate):
    result = crud.delete_expense(paylaod.category, paylaod.description, paylaod.amount)
    if not result["success"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result["message"])
    return result

@app.get("/expenses/category/{category}", status_code=status.HTTP_200_OK)
def api_get_expenese_by_category(category: str):
    result = crud.get_expense_category(category)
    if result["status"] == "not_found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=result["message"])
    return result["data"]

@app.get("/expenses/stats", status_code=status.HTTP_200_OK)
def api_get_status():
    result = crud.get_expense_stats()
    return result["data"]
"""




'''
def main():
 
    
    while True:
        print("\n--- EXPENSE MANAGEMENT INTERFACE ---")
        print("[1] Add Expense")
        print("[2] Show Expenses")
        print("[3] Delete Expense")
        print("[4] Exit")

        userinput = input("\n>>> Select Option: ")

        if userinput == "1":
            add_expense()

        elif userinput == "2":
            show_expenses()

        elif userinput == "3":
            delete_expense()

        elif userinput == "4":
            print("Goodbye!")
            break 
        else:
            print("Invalid option! Please enter 1, 2, 3, or 4.")
'''
