from pydantic import BaseModel
from datetime import date


class ExpenseBase(BaseModel):
    category: str
    description: str
    amount: float
    date: date

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(ExpenseBase):
    pass