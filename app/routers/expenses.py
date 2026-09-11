from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.models.user import DBUser
from app.models.expense import DBExpense
from app.routers.auth import get_current_user
from app.services.security_guardrails import check_rate_limiting_guardrail
from app.services.rag_engine import run_langchain_rag_pipeline

router = APIRouter(prefix="/expenses", tags=["Live PostgreSQL Tracker Channels"])

@router.post("/log-expense")
async def record_user_transaction_with_ai_audit(
    amount: float,
    category: str,
    description: str,
    current_user: DBUser = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    username = getattr(current_user, "username", "Unknown User")
    check_rate_limiting_guardrail(username)
    
    audit_query = f"What is the maximum allowed spending limit cap threshold code rule for {category}?"
    rag_payload = await run_langchain_rag_pipeline(query=audit_query, active_username=username)
    ai_verdict = rag_payload.get("ai_generated_answer", "")
    
    new_expense = DBExpense(
        amount=amount,
        category=category.title().strip(),
        description=description,
        user_id=current_user.id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    
    return {
        "status": "TRANSACTION_RECORDED",
        "expense_id": new_expense.id,
        "amount": new_expense.amount,
        "category": new_expense.category,
        "compliance_audit_summary": ai_verdict
    }
