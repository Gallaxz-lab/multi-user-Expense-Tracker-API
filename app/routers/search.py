from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Dict, Any, List

from app.database.connection import get_db
from app.routers.auth import get_current_user
import app.models.user as models_user
from app.models.expense import Expense

from app.services.document_processor import extract_and_chunk_pdf
from app.services.vector_store import add_uploaded_pdf_to_real_indices, run_real_semantic_search, run_real_keyword_search, clear_all_indexed_documents_store
from app.services.rag_engine import run_pdf_assistant_pipeline, run_real_hybrid_fusion, run_production_reranker


router = APIRouter(prefix="/search", tags=["Hybrid RAG & PDF Assistant"])

# =====================================================================
# ENDPOINT 1: UPLOAD AND PROCESS PDF 
# =====================================================================
@router.post("/upload-pdf")
async def upload_real_pdf_document(file: UploadFile = File(...)):
    """Uploads real files, extracts pages, and loads true BM25 and Vector indices."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only standard PDF files allowed.")
    try:
        bytes_data = await file.read()
        chunks = extract_and_chunk_pdf(bytes_data, file.filename)
        if not chunks:
            return {"message": "No indexable content found inside document."}
            
        add_uploaded_pdf_to_real_indices(chunks)
        return {"filename": file.filename, "total_indexed_chunks": len(chunks)}
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))

# =====================================================================
# ENDPOINT 2: ASK QUESTIONS & INSPECT CHUNKS
# =====================================================================


@router.get("/ask")
async def ask_questions_and_receive_citations(
    query: str = Query(..., min_length=2, description="Ask questions about your uploaded PDFs"),
    top_k: int = Query(3, ge=1, le=5)
) -> Dict[str, Any]:
    """Queries your document knowledge base and returns a grounded answer with diagnostics."""
    try:
        result = await run_pdf_assistant_pipeline(query=query, top_k=top_k)
        return result
    except Exception as err:
        raise HTTPException(status_code=502, detail=str(err))
    
    
# =====================================================================
# ENDPOINT 3: ASK QUESTIONS & INSPECT CHUNKS
    # =====================================================================
    
    
@router.get("/compare")
async def compare_real_file_retrievals(
    query: str = Query(..., min_length=2),
    top_k: int = Query(3, ge=1, le=5)
) -> Dict[str, Any]:
    """Compares genuine BM25 math and Gemini Vector search profiles side-by-side."""
    keyword_out = run_real_keyword_search(query, top_k=top_k)
    semantic_out = run_real_semantic_search(query, top_k=top_k)
    hybrid_out = run_real_hybrid_fusion(query, limit=top_k)
    
    broader_pool = run_real_hybrid_fusion(query, limit=6)
    reranked_out = await run_production_reranker(query, broader_pool, top_k=top_k)
    
    return {
        "evaluation_query": query,
        "real_keyword_bm25_output": keyword_out,
        "real_semantic_vector_output": semantic_out,
        "real_hybrid_fusion_output": hybrid_out,
        "real_reranked_pipeline_output": reranked_out
    }
    
@router.delete("/reset-knowledge-base")
def reset_pdf_knowledge_base_indices():
    """[CLEAR PDF ENGINE DATABASE] Manually flushes all uploaded document text chunks and vector embeddings."""
    try:
        clear_all_indexed_documents_store()
        return {
            "status": "SUCCESS",
            "message": "All text chunks and vector embeddings have been securely wiped from memory indices."
        }
    except Exception as err:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while attempting to wipe knowledge cache layers: {str(err)}"
        )