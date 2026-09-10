from fastapi import APIRouter, UploadFile, File, Query, HTTPException, Depends
from typing import Dict, Any

# Ingestion, Vector, and Generation Pipeline Service Imports
from app.services.document_processor import process_uploaded_pdf_to_langchain_docs
from app.services.vector_store import add_docs_to_langchain_retrievers, clear_all_langchain_retrievers
from app.services.rag_engine import run_langchain_rag_pipeline

# LangGraph Support Agent and Login Security Imports
from app.services.graph_builder import compiled_support_graph
from app.routers.auth import get_current_user  # Real JWT session token validator

# Security Tier Guardrail Imports
from app.schemas.support_state import UserSupportQueryInputSchema
from app.services.security_guardrails import (
    check_rate_limiting_guardrail,
    sanitize_prompt_injection_guardrail,
    validate_payload_size_limits
)

router = APIRouter(prefix="/search", tags=["Secured Enterprise RAG Hub"])

# =====================================================================
# 1. SECURED PDF DOCUMENT UPLOAD INGESTION ENDPOINT
# =====================================================================
@router.post("/upload-pdf")
async def upload_and_index_to_azure_cloud(
    file: UploadFile = File(...),
    current_user: Any = Depends(get_current_user) # 🔐 AUTHENTICATION REQUIRED
):
    """Securely uploads raw files with strict memory payload size restrictions."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only standard PDF assets allowed.")
        
    # ⏱️ RATE LIMITING PROTECTION CHECK
    check_rate_limiting_guardrail(current_user.username)
    
    try:
        file_bytes = await file.read()
        
        # 🛡️ REQUEST SIZE LIMIT PROTECTION: Blocks buffer exploits above 5MB max
        validate_payload_size_limits(file_bytes, max_mb=5)
        
        langchain_documents = process_uploaded_pdf_to_langchain_docs(file_bytes, file.filename, current_user.username)
        if not langchain_documents:
            return {"message": "No extractable sections captured."}
            
        add_docs_to_langchain_retrievers(langchain_documents)
        return {
            "status": "SUCCESS",
            "filename": file.filename, 
            "total_chunks_pushed_to_azure_search": len(langchain_documents)
        }
    except HTTPException as handled_api_err:
        raise handled_api_err
    except Exception:
        print(f"❌ [Upload Exception]: Wiped trace stack details to hide sensitive data.")
        raise HTTPException(status_code=500, detail="Internal server ingestion failure encountered.")


# =====================================================================
# 2. SECURED STRUCTURED CONVERSATIONAL RAG SEARCH ENDPOINT
# =====================================================================
@router.get("/ask")
async def query_azure_rag_pipeline_with_structured_output(
    current_user: Any = Depends(get_current_user),
    input_data: UserSupportQueryInputSchema = Depends(),
    top_k: int = Query(4, ge=1, le=5)
) -> Dict[str, Any]:
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    username = getattr(current_user, "username", "Unknown User")
    check_rate_limiting_guardrail(username)
    clean_user_query = sanitize_prompt_injection_guardrail(input_data.query)
    
    try:
        result = await run_langchain_rag_pipeline(query=clean_user_query, active_username=username, top_k=top_k)
        return result
    except Exception:
        raise HTTPException(status_code=502, detail="Isolated system retrieval exception logged.")


# =====================================================================
# 3. SECURED INTELLIGENT ROUTER AGENT WORKFLOW (LANGGRAPH)
# =====================================================================
@router.get("/smart-support")
async def intelligent_support_router_endpoint(
    current_user: Any = Depends(get_current_user),
    input_data: UserSupportQueryInputSchema = Depends()
):
    
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
        
    username = getattr(current_user, "username", "Unknown User")
    check_rate_limiting_guardrail(username)
    
    clean_user_query = sanitize_prompt_injection_guardrail(input_data.query)
    
    try:
        role = getattr(current_user, "role", "User")
        is_active = getattr(current_user, "is_active", True)
        
        user_context_dict = {
            "username": username,
            "role": role,
            "is_active": is_active
        }
        
        initial_state = {
            "user_query": clean_user_query,
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
            "user_query": clean_user_query,
            "logged_in_username_detected": user_context_dict["username"],
            "successful_tools_run": final_output_state.get("executed_tools"),
            "agent_response": final_output_state.get("final_response"),
            "total_iterations_run": final_output_state.get("loop_count")
        }
    except Exception:
        raise HTTPException(status_code=502, detail="Agent system core operational exception logged.")


# =====================================================================
# 4. SECURED CLEAR KNOWLEDGE BASE ENDPOINT (ADMINS ONLY BLOCKER)
# =====================================================================
@router.delete("/reset-knowledge-base")
def reset_pdf_knowledge_base_indices(
    current_user: Any = Depends(get_current_user) # 🔐 AUTHENTICATION REQUIRED
):
    """[CLEAR CLOUD DATABASE] Securely flushes all records. Restricted to Admin roles."""
    
    # ⏱️ RATE LIMITING PROTECTION CHECK
    check_rate_limiting_guardrail(current_user.username)
    
    # 🛡️ RBAC ROLE-BASED ACCESS CONTROL GATEWAY BLOCKER:
    # Verifies that only users explicitly labeled as 'Admin' inside your db can drop tables!
    user_role = getattr(current_user, "role", "User")
    if user_role.lower() != "admin":
        print(f"🛑 [Security Alert] Non-admin user '{current_user.username}' attempted to wipe cloud indices!")
        raise HTTPException(
            status_code=403, 
            detail="Forbidden: Admin level security clearance role required to perform database wipe operations."
        )
        
    try:
        clear_all_langchain_retrievers()
        return {
            "status": "SUCCESS",
            "message": "All text chunks and vector embeddings have been securely wiped from your Azure AI Search cloud index."
        }
    except Exception:
        raise HTTPException(status_code=500, detail="An error occurred while attempting to wipe cloud index records.")
