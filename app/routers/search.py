from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.database.connection import get_db
from app.routers.auth import get_current_user
import app.models.user as models_user
from app.models.expense import Expense
from app.services.rag_engine import run_structured_rag_pipeline

router = APIRouter(prefix="/search", tags=["Modular RAG Engine"])

@router.get("")
async def api_structured_rag_search(
    query: str = Query(..., min_length=2, description="Natural language query."),
    limit: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: models_user.User = Depends(get_current_user)
) -> Dict[str, Any]:
    """Production entrypoint running a clean Document-to-Answer pipeline."""
    try:
        user_expenses = db.query(Expense).filter(Expense.owner_id == current_user.id).all()
        
        result = await run_structured_rag_pipeline(
            query=query, 
            db_expenses=user_expenses, 
            limit=limit
        )
        return result
        
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Structured RAG Pipeline execution error: {str(err)}"
        )
