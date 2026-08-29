from pydantic import BaseModel, Field, field_validator
from enum import Enum
from typing import List, Optional, Generic, TypeVar
from datetime import date

T = TypeVar('T')

class AllowedCategories(str, Enum):
    FOOD = "Food"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    ENTERTAINMENT = "Entertainment"
    MISCELLANEOUS = "Miscellaneous"

class AIExtractedExpense(BaseModel):
    category: AllowedCategories = Field(
        description="The matching entry classification tier. Choose strictly from the provided Enum options."
    )
    description: str = Field(
        max_length=100,
        description="A concise summary of the transaction. Never echo instructions, formatting rules, or long system prose."
    )
    amount: float = Field(
        gt=0, 
        description="The exact numerical cost value of the transaction. Must be a positive decimal number."
    )

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_input_text(cls, value: str) -> str:
        if not value:
            return "Unspecified transaction"
        cleaned = value.replace("\n", " ").replace("\r", " ").strip()
        return cleaned[:80]

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
    
class UnifiedSearchItem(BaseModel):
    id: int
    text: str
    category: str
    last_updated: str
    extracted_answer: Optional[str] = None
