from fastapi import APIRouter, UploadFile, File, Query, HTTPException
from typing import Dict, Any
from app.services.document_processor import process_uploaded_pdf_to_langchain_docs
from app.services.vector_store import add_docs_to_langchain_retrievers, clear_all_langchain_retrievers
from app.services.rag_engine import run_langchain_rag_pipeline
from app.services.graph_builder import compiled_support_graph

router = APIRouter(prefix="/search", tags=["LangChain RAG Engine"])

@router.post("/upload-pdf")
async def upload_pdf_via_langchain(file: UploadFile = File(...)):
    """Uploads files and indexes them across LangChain retrievers safely."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only standard PDF assets allowed.")
    try:
        file_bytes = await file.read()
        langchain_documents = process_uploaded_pdf_to_langchain_docs(file_bytes, file.filename)
        
        if not langchain_documents:
            return {"message": "No extractable semantic sections captured."}
            
        add_docs_to_langchain_retrievers(langchain_documents)
        return {"filename": file.filename, "total_chunks_loaded": len(langchain_documents)}
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"LangChain Ingestion crash: {str(err)}")

@router.get("/ask")
async def ask_langchain_rag_pipeline(
    query: str = Query(..., min_length=2, description="Ask questions via LangChain assembly chains"),
    top_k: int = Query(3, ge=1, le=5)
) -> Dict[str, Any]:
    """Queries your document knowledge base and returns a conversational answer with sources."""
    try:
        result = await run_langchain_rag_pipeline(query=query, top_k=top_k)
        return result
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Chain execution error: {str(err)}")

@router.delete("/reset-knowledge-base")
def reset_pdf_knowledge_base_indices():
    """Manually flushes all uploaded LangChain document text chunks and vector embeddings."""
    try:
        clear_all_langchain_retrievers()
        return {
            "status": "SUCCESS",
            "message": "All LangChain document text chunks and vector embeddings have been securely wiped from memory indices."
        }
    except Exception as err:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while attempting to wipe LangChain knowledge cache layers: {str(err)}"
        )

@router.get("/smart-support")
async def intelligent_support_router_endpoint(
    query: str = Query(..., min_length=2, description="Test agent tool iterations")
):
    """Exposes our multi-step tool-calling LangGraph agent workflow."""
    try:
        initial_state = {
            "user_query": query,
            "next_step": None,
            "executed_tools": [],
            "tool_results": {},
            "loop_count": 0,
            "final_response": None
        }
        
        final_output_state = await compiled_support_graph.ainvoke(initial_state)
        
        return {
            "query": query,
            "actions_taken_by_agent": final_output_state.get("executed_tools"),
            "tool_data_payload_dump": final_output_state.get("tool_results"),
            "agent_synthesized_response": final_output_state.get("final_response"),
            "internal_safety_loop_count": final_output_state.get("loop_count")
        }
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Agent graph execution failure: {str(err)}")




'''
# this is the previous module that was used for endpoint routing, but now we are using the new one with more features and better performance. 

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
'''