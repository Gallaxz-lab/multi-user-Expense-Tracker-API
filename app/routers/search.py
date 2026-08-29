from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import asyncio # Crucial for parallelizing network calls

from google import genai
from google.genai import types
from app.config import settings
from app.database.connection import get_db
from app.routers.auth import get_current_user
import app.models.user as models_user
import app.schemas.expense as schemas_exp
from app.models.expense import Expense
from app.services.semantic_search import search_unified_knowledge
import re

router = APIRouter(prefix="/search", tags=["Hybrid Semantic Search"])
ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

class UnifiedSearchItem(BaseModel):
    id: int
    category: str 
    last_updated: str
    extracted_answer: Optional[str] = None
    text: str
    
class UnifiedSearchResponse(BaseModel):
    score: float
    source: str
    data: UnifiedSearchItem

# Helper coroutine to execute LLM calls concurrently
import re

async def extract_document_context(query: str, doc_text: str) -> str:
    prompt_context = (
        f"Document Source Text:\n{doc_text}\n\n"
        f"User Question: '{query}'\n\n"
        f"Task: Extract only the specific line or guideline sentence from the Document Source Text "
        f"that directly answers the User Question. Do not include unrelated guidelines. Output only the exact text matching."
    )
    try:
        # 1. Use the universally supported production standard flash string identifier
        response = await ai_client.models.generate_content_async(
            model='gemini-2.5-flash', 
            contents=prompt_context,
            config=types.GenerateContentConfig(
                temperature=0.0,
                system_instruction=(
                    "You are a strict data extraction utility. Return ONLY the exact text slice "
                    "from the document that matches the context of the user question. Do not summarize."
                )
            )
        )
        answer = response.text.strip() if response.text else ""
        if answer and len(answer) > 5:
            return answer
            
    except Exception as api_err:
        print(f"⚠️ Gemini extraction extraction failed ({str(api_err)}). Activating local fallback mechanism...")

    # ---- SMART LOCAL FALLBACK MECHANISM ----
    # If the LLM pipeline crashes, search locally line-by-line for words like "meal" or "allowance" 
    # instead of just blindly slicing the top of the file ("1. Travel Expenses...")
    query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 3]
    lines = doc_text.split('\n')
    
    for line in lines:
        if any(word in line.lower() for word in query_words):
            return line.strip() # Returns the actual matching row line dynamically (e.g., Row #2)

    # Absolute baseline fallback if no keywords overlap
    if len(doc_text) <= 120:
        return doc_text
    return doc_text[:120].strip() + "..."

@router.get("", response_model=schemas_exp.StandardResponse[List[UnifiedSearchResponse]])
async def api_hybrid_semantic_search( # Changed to async def to handle non-blocking IO loops
    query: str = Query(..., min_length=2, description="Natural sentence query targeting docs or finances."),
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: models_user.User = Depends(get_current_user)
):
    try:
        # 1. Fetch user records from PostgreSQL
        user_expenses = db.query(Expense).filter(Expense.owner_id == current_user.id).all()
        
        # 2. Run vector closeness search
        raw_results = search_unified_knowledge(query=query, db_expenses=user_expenses, top_k=limit)
        
        processed_results = []
        tasks = []
        task_indices = []

        for idx, item in enumerate(raw_results):
            if item["source"] == "User Financial Record":
                processed_results.append({
                    "score": item["score"],
                    "source": item["source"],
                    "data": {
                        "id": item["data"]["id"],
                        "category": item["data"]["category"],
                        "last_updated": item["data"]["last_updated"],
                        "extracted_answer": item["data"]["text"],
                        "text": item["data"]["text"]
                    }
                })
            else:
                # Placeholder for document that needs async LLM extraction
                processed_results.append(item) 
                tasks.append(extract_document_context(query, item["data"]["text"]))
                task_indices.append(idx)

        # Execute all API extraction requests concurrently
        if tasks:
            extracted_answers = await asyncio.gather(*tasks)
            for idx, answer in zip(task_indices, extracted_answers):
                item = processed_results[idx]
                processed_results[idx] = {
                    "score": item["score"],
                    "source": item["source"],
                    "data": {
                        "id": item["data"]["id"],
                        "category": item["data"]["category"],
                        "last_updated": item["data"]["last_updated"],
                        "extracted_answer": answer,
                        "text": item["data"]["text"],
                    }
                }
            
        return schemas_exp.StandardResponse(
            message="Unified vector analytics and contextual text extraction complete.",
            data=processed_results
        )
    except Exception as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Vector extraction pipeline crashed: {str(err)}"
        )
