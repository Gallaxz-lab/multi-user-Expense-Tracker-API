from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class ExpenseBase(BaseModel):
    amount: float = Field(..., gt=0)
    category: str = Field(..., min_length=2, max_length=100)
    description: str = Field(..., min_length=3, max_length=255)

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = Field(None, min_length=3, max_length=255)

class ExpenseResponse(ExpenseBase):
    id: int
    timestamp: datetime
    user_id: int

    class Config:
        from_attributes = True
