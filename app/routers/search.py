from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends
from typing import Dict, Any

# Ingestion, Vector, and Generation Pipeline Service Imports
from app.services.document_processor import process_uploaded_pdf_to_langchain_docs
from app.services.vector_store import add_docs_to_langchain_retrievers, clear_all_langchain_retrievers
from app.services.rag_engine import run_langchain_rag_pipeline

# LangGraph Support Agent and Login Security Imports
from app.services.graph_builder import compiled_support_graph
from app.routers.auth import get_current_user  

router = APIRouter(prefix="/search", tags=["Enterprise Cloud RAG Hub"])

@router.post("/upload-pdf")
async def upload_and_index_to_azure_cloud(
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_user) # Extracts the logged-in user profile
):
    """Securely uploads raw files to Azure Storage and writes user-isolated chunks to Azure AI Search."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only standard PDF assets allowed.")
    try:
        file_bytes = await file.read()
        
        # Injects current_user.username into metadata properties on ingestion
        langchain_documents = process_uploaded_pdf_to_langchain_docs(file_bytes, file.filename, current_user.username)
        
        if not langchain_documents:
            return {"message": "No extractable sections captured."}
            
        add_docs_to_langchain_retrievers(langchain_documents)
        return {
            "status": "SUCCESS",
            "filename": file.filename, 
            "indexed_owner": current_user.username,
            "total_chunks_pushed_to_azure_search": len(langchain_documents)
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"Cloud Ingestion failed: {str(err)}")


@router.get("/ask")
async def query_azure_rag_pipeline_with_structured_output(
    query: str = Query(..., min_length=2, description="Ask questions about your uploaded cloud documents"),
    top_k: int = Query(4, ge=1, le=5),
    current_user: Any = Depends(get_current_user)
) -> Dict[str, Any]:
    """Queries Azure AI Search with metadata filters and runs an observability-tracked generation pass."""
    try:
        result = await run_langchain_rag_pipeline(query=query, active_username=current_user.username, top_k=top_k)
        print(f"🏁 [Request Completed] ID: {result.get('observability_request_id')} | Successfully generated response back to user.")
        return result
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Pipeline exception: {str(err)}")


@router.delete("/reset-knowledge-base")
def reset_pdf_knowledge_base_indices(current_user: Any = Depends(get_current_user)):
    """Manually flushes all indexed records from Azure AI Search."""
    try:
        clear_all_langchain_retrievers()
        return {
            "status": "SUCCESS",
            "message": "All text chunks and vector embeddings have been securely wiped from your Azure AI Search cloud index."
        }
    except Exception as err:
        raise HTTPException(status_code=500, detail=f"An error occurred while attempting to wipe cloud caches: {str(err)}")


@router.get("/smart-support")
async def intelligent_support_router_endpoint(
    query: str = Query(..., min_length=2, description="Test agent failure modes and guardrails resilience parameters"),
    current_user: Any = Depends(get_current_user) 
):
    """API entrypoint executing a safety-hardened tool-calling graph agent architecture."""
    try:
        # Extract live authenticated details directly out of your user database table record profile
        username = getattr(current_user, "username", current_user.get("username") if isinstance(current_user, dict) else "Unknown User")
        role = getattr(current_user, "role", "User")
        is_active = getattr(current_user, "is_active", True)
        
        user_context_dict = {
            "username": username,
            "role": role,
            "is_active": is_active
        }
        
        # Initialize properties matching our SupportRouterState schema
        initial_state = {
            "user_query": query,
            "current_user": user_context_dict,
            "next_step": None,
            "executed_tools": [],
            "tool_results": {},
            "tool_error_logs": [],
            "loop_count": 0,
            "security_clearance_blocked": False,
            "human_escalation_required": False,
            "final_response": None
        }
        
        final_output_state = await compiled_support_graph.ainvoke(initial_state)
        
        return {
            "user_query": query,
            "logged_in_username_detected": user_context_dict["username"],
            "successful_tools_run": final_output_state.get("executed_tools"),
            "tool_results_data_dump": final_output_state.get("tool_results"),
            "system_caught_error_logs": final_output_state.get("tool_error_logs"),
            "security_breach_blocked": final_output_state.get("security_clearance_blocked"),
            "human_staff_escalated": final_output_state.get("human_escalation_required"),
            "agent_response": final_output_state.get("final_response"),
            "total_iterations_run": final_output_state.get("loop_count")
        }
    except Exception as err:
        raise HTTPException(status_code=502, detail=f"Agent system core error: {str(err)}")