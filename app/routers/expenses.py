from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.database.connection import get_db
import app.schemas.expense as schemas_exp
import app.services.crud as crud
from app.routers.auth import get_current_user
import app.models.user as models_user

from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from app.config import settings


ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

class AIExtractedExpense(BaseModel):
    category: str = Field(description="The financial category matching the item like Food, Transport, Utilities, Entertainment, or Miscellaneous.")
    description: str = Field(description="A concise summary of what the money was spent on.")
    amount: float = Field(description="The numerical cost value extracted from the text string statement.")

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.post("", response_model=schemas_exp.StandardResponse[schemas_exp.ExpenseResponse], status_code=status.HTTP_201_CREATED)
def api_add_expense(payload: schemas_exp.ExpenseCreate, db: Session = Depends(get_db), current_user: models_user.User = Depends(get_current_user)):
    res = crud.add_expense(db, payload.category, payload.description, payload.amount, payload.date, current_user.id)
    mapped = schemas_exp.ExpenseResponse(id=res["data"].id, category=payload.category, description=res["data"].description, amount=res["data"].amount, date=res["data"].date)
    return schemas_exp.StandardResponse(message=res["message"], data=mapped)

@router.get("", response_model=schemas_exp.StandardResponse[List[schemas_exp.ExpenseResponse]])
def api_show_expenses(
    limit: int = Query(10, ge=1, le=100), offset: int = Query(0, ge=0), sort: str = Query("date"), order: str = Query("desc"),
    db: Session = Depends(get_db), current_user: models_user.User = Depends(get_current_user)
):
    records = crud.show_expenses(db, current_user.id, limit, offset, sort, order)
    mapped = [schemas_exp.ExpenseResponse(id=r.id, category=r.category_rel.name, description=r.description, amount=r.amount, date=r.date) for r in records]
    return schemas_exp.StandardResponse(message="Expenses retrieved successfully", data=mapped)

@router.delete("", response_model=schemas_exp.StandardResponse)
def api_delete_expense(payload: schemas_exp.ExpenseCreate, db: Session = Depends(get_db), current_user: models_user.User = Depends(get_current_user)):
    res = crud.delete_expense_by_match(db, payload.category, payload.description, payload.amount, current_user.id)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["message"])
    return schemas_exp.StandardResponse(message=res["message"])

@router.put("/{id}", response_model=schemas_exp.StandardResponse[schemas_exp.ExpenseResponse])
def api_update_expense(id: int, payload: schemas_exp.ExpenseUpdate, db: Session = Depends(get_db), current_user: models_user.User = Depends(get_current_user)):
    res = crud.update_expense_by_id(db, id, payload.category, payload.description, payload.amount, payload.date, current_user.id)
    if res["status"] == "not_found":
        raise HTTPException(status_code=404, detail=res["message"])
    mapped = schemas_exp.ExpenseResponse(id=res["data"].id, category=payload.category, description=res["data"].description, amount=res["data"].amount, date=res["data"].date)
    return schemas_exp.StandardResponse(message=res["message"], data=mapped)


@router.get("/category/{category}", response_model=schemas_exp.StandardResponse[List[schemas_exp.ExpenseResponse]])
def api_get_expenses_by_category(category: str, db: Session = Depends(get_db), current_user: models_user.User = Depends(get_current_user)):
    res = crud.get_expenses_by_category(db, category, current_user.id)
    if res["status"] == "not_found":
        raise HTTPException(status_code=404, detail=res["message"])
    mapped = [schemas_exp.ExpenseResponse(id=r.id, category=category, description=r.description, amount=r.amount, date=r.date) for r in res["data"]]
    return schemas_exp.StandardResponse(message="Data successfully parsed", data=mapped)

@router.get("/stats", response_model=schemas_exp.StandardResponse[schemas_exp.ExpenseStatsData])
def api_get_expenses_stats(db: Session = Depends(get_db), current_user: models_user.User = Depends(get_current_user)):
    res = crud.get_expense_stats(db, current_user.id)
    return schemas_exp.StandardResponse(message="Stats compiled successfully", data=res["data"])

@router.get("/search", response_model=schemas_exp.StandardResponse[List[schemas_exp.ExpenseResponse]])
def api_search_expenses(keyword: str, db: Session = Depends(get_db), current_user: models_user.User = Depends(get_current_user)):
    if not keyword.strip():
        return schemas_exp.StandardResponse(message="Empty keyword mapping", data=[])
    records = crud.search_expenses(db, keyword, current_user.id)
    mapped = [schemas_exp.ExpenseResponse(id=r.id, category=r.category_rel.name, description=r.description, amount=r.amount, date=r.date) for r in records]
    return schemas_exp.StandardResponse(message="Search parameters processed", data=mapped)

@router.post("/ai-add", response_model=schemas_exp.StandardResponse[schemas_exp.ExpenseResponse])
def api_ai_add_expense(
    prompt: str, 
    db: Session = Depends(get_db), 
    current_user: models_user.User = Depends(get_current_user)
):
    try:
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Extract the expense metadata fields out of this user narrative statement: '{prompt}'",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AIExtractedExpense,
                temperature=0.1
            ),
        )
        extracted_data = AIExtractedExpense.model_validate_json(response.text)

    except Exception as ai_err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"The AI operational processing agent failed to parse text attributes: {str(ai_err)}"
        )

    try:
        res = crud.add_expense(
            db, 
            category=extracted_data.category, 
            description=extracted_data.description, 
            amount=extracted_data.amount, 
            expense_date=date.today(), 
            owner_id=current_user.id
        )

        mapped = schemas_exp.ExpenseResponse(
            id=res["data"].id, 
            category=extracted_data.category, 
            description=res["data"].description, 
            amount=res["data"].amount, 
            date=res["data"].date
        )
        return schemas_exp.StandardResponse(message="AI verified and recorded entry successfully", data=mapped)

    except Exception as db_err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI data extraction was successful, but database insertion failed: {str(db_err)}"
        )
