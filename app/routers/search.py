from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import json

from google import genai
from google.genai import types
from app.config import settings
from app.database.connection import get_db
from app.routers.auth import get_current_user
import app.models.user as models_user
import app.schemas.expense as schemas_exp
from app.models.expense import Expense
from app.services.semantic_search import search_unified_knowledge

router = APIRouter(prefix="/search", tags=["Hybrid Semantic Search"])

# Initialize the Gemini client inside the router scope
ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

class UnifiedSearchItem(BaseModel):
    id: int
    text: str
    category: str
    last_updated: str
    extracted_answer: Optional[str] = None

class UnifiedSearchResponse(BaseModel):
    score: float
    source: str
    data: UnifiedSearchItem

@router.get("", response_model=schemas_exp.StandardResponse[List[UnifiedSearchResponse]])
def api_hybrid_semantic_search(
    query: str = Query(..., min_length=2, description="Natural sentence query targeting docs or finances."),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: models_user.User = Depends(get_current_user)
):
    try:
        # 1. Fetch user records from PostgreSQL
        user_expenses = db.query(Expense).filter(Expense.owner_id == current_user.id).all()
        
        # 2. Run raw math cosine vector closeness search
        raw_results = search_unified_knowledge(query=query, db_expenses=user_expenses, top_k=limit)
        
        processed_results = []
        for item in raw_results:
            # ---- BLOCK A: For User Financial Database Records ----
            if item["source"] == "User Financial Record":
                processed_results.append({
                    "score": item["score"],
                    "source": item["source"],
                    "data": {
                        "id": item["data"]["id"],
                        "category": item["data"]["category"],
                        "last_updated": item["data"]["last_updated"],
                        "extracted_answer": item["data"]["text"], # Sets extracted_answer right before text
                        "text": item["data"]["text"]
                    }
                })
                continue
                
            # ---- LLM RERANKING & EXTRACTION FILTER PHASE (For Long System Docs) ----
            full_document_text = item["data"]["text"]
            
            prompt_context = (
                f"Document Source Text:\n{full_document_text}\n\n"
                f"User Question: '{query}'\n\n"
                f"Task: Extract only the exact sentences or guidelines from the document that directly answer "
                f"the User Question. Do not summarize or add external commentary. If no specific section applies, "
                f"extract the most matching sentence."
            )
            
            try:
                # Ask Gemini to isolate the specific text chunk matching the query context
                ai_extraction = ai_client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=prompt_context,
                    config=types.GenerateContentConfig(
                        temperature=0.0 # Strict accuracy parameter removes hallucinations
                    )
                )
                clean_snippet = ai_extraction.text.strip()
            except Exception:
                # Fallback to the first 120 characters if the AI model pipeline fails
                clean_snippet = full_document_text[:120] + "..."

            processed_results.append({
                "score": item["score"],
                "source": item["source"],
                "data": {
                    "id": item["data"]["id"],
                    "category": item["data"]["category"],
                    "last_updated": item["data"]["last_updated"],
                    "extracted_answer": clean_snippet, 
                    "text": full_document_text,
                }
            })
            
        return schemas_exp.StandardResponse(
            message="Unified vector analytics and contextual text extraction complete.",
            data=processed_results
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vector extraction pipeline crashed: {str(err)}"
        )
