from pydantic import BaseModel, Field
from typing import List, Optional, Generic, TypeVar
from datetime import date

T = TypeVar('T')

class StandardResponse(BaseModel, Generic[T]):
    status: str = "success"
    message: str
    data: Optional[T] = None

class ExpenseBase(BaseModel):
    category: str
    description: str
    amount: float
    date: date

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(ExpenseBase):
    pass

class ExpenseResponse(BaseModel):
    id: int
    category: str
    description: str
    amount: float
    date: date

    class Config:
        from_attributes = True

class ExpenseStatsData(BaseModel):
    total_expenses: int
    total_amount: float
    average_amount: float
    highest_expense: Optional[dict] = None
