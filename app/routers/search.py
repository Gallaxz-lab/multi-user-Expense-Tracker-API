from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database.connection import get_db
from app.routers.auth import get_current_user
import app.models.user as models_user
from app.models.expense import Expense

from app.services.document_processor import extract_and_chunk_pdf
from app.services.vector_store import add_chunks_to_vector_store
from app.services.rag_engine import run_pdf_assistant_pipeline

router = APIRouter(prefix="/search", tags=["Hybrid RAG & PDF Assistant"])

# =====================================================================
# ENDPOINT 1: UPLOAD AND PROCESS PDF 
# =====================================================================
@router.post("/upload-pdf")
async def upload_and_process_pdf_file(
    file: UploadFile = File(...),
    current_user: models_user.User = Depends(get_current_user)
):
    """Uploads a PDF file, slices it into semantic chunks, and stores its embeddings."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only standard .pdf files are accepted.")
    try:
        content_bytes = await file.read()
        chunks = extract_and_chunk_pdf(content_bytes, file.filename)
        
        if not chunks:
            return {"message": "PDF uploaded but no readable text chunks could be extracted."}
            
        add_chunks_to_vector_store(chunks)
        return {
            "message": "PDF successfully processed and stored in vector index memory.",
            "filename": file.filename,
            "total_chunks_extracted": len(chunks)
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"PDF extraction worker failed: {str(err)}")

# =====================================================================
# ENDPOINT 2: ASK QUESTIONS & INSPECT CHUNKS
# =====================================================================
@router.get("/ask")
async def ask_questions_about_pdf(
    query: str = Query(..., min_length=2, description="Ask questions about your uploaded PDFs"),
    top_k: int = Query(4, ge=1, le=10),
    current_user: models_user.User = Depends(get_current_user)
) -> Dict[str, Any]:
    try:
        result = await run_pdf_assistant_pipeline(query=query, top_k=top_k)
        return result
    except Exception as err:
        raise HTTPException(status_code=502, detail=str(err))
