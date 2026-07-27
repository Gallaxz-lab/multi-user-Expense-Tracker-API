from database import show_expenses, add_expense, delete_expense,update_expense, init_db
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from datetime import date

app = FastAPI(title="Expense Tracker Advanced API")

init_db()

class Expensepayloaad(BaseModel):
    category: str
    description: str
    amount: float
    date: date

class ExpenseUpdatePayload(BaseModel):
    id: int
    category: str
    description: str
    amount: float
    date: date

@app.post("/expense")
def api_add_expense(payload: Expensepayloaad):
    result = add_expense(payload.category, payload.description, payload.amount, payload.date)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.put("/expense")
def api_put_expense(paylaod: ExpenseUpdatePayload):
    result = update_expense(paylaod.id, paylaod.category, paylaod.description, paylaod.amount, paylaod.date)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@app.get("/expense")
def api_show_expense():
    return show_expenses()

@app.delete("/expense")
def api_delete_expense(paylaod: Expensepayloaad):
    result = delete_expense(paylaod.category, paylaod.description, paylaod.amount)
    if not result["success"]:
            raise HTTPException(status_code=400, detail=result["message"])
    return result

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
    



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
