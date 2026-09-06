import asyncio
from typing import Dict, Any
from app.services.rag_engine import run_langchain_rag_pipeline

def get_customer_info_authenticated(user_profile: Dict[str, Any]) -> Dict[str, Any]:
    if not user_profile or "username" not in user_profile:
        return {
            "is_error": True,
            "error_type": "AUTHENTICATION_ERROR",
            "message": "Security Verification Failed: No active logged-in user session context found."
        }
    
    username = user_profile.get("username")
    role = user_profile.get("role", "User")
    is_active = user_profile.get("is_active", True)
    
    if not is_active:
        return {
            "is_error": True,
            "error_type": "ACCOUNT_SUSPENDED",
            "message": f"Security Block: The account for user '{username}' is currently suspended."
        }
        
    return {
        "is_error": False, 
        "data": {
            "name": username, 
            "tier": role, 
            "status": "Active"
        }
    }


def search_knowledge_base(query: str) -> Dict[str, Any]:
    """Tool: Runs full-text and semantic checks over the FAISS + BM25 disk indexes."""
    # ─── TOOL INPUT VALIDATION ───
    if not query or len(query.strip()) < 3:
        return {
            "is_error": True,
            "error_type": "VALIDATION_ERROR",
            "message": "Malformed Tool Input: Search query string must be at least 3 characters long."
        }
        
    print(f"🔍 [Tool Execution: RAG] Scanning FAISS directories for: '{query}'")
    try:
        rag_payload = asyncio.run(run_langchain_rag_pipeline(query=query, top_k=2))
        answer = rag_payload.get("answer", "")
        
        if "cannot find the answer" in answer.lower() or not answer.strip():
            return {
                "is_error": True,
                "error_type": "EMPTY_RESULT",
                "message": "No documentation entries matched this query profile in our indexes."
            }
            
        return {"is_error": False, "context": answer, "sources": rag_payload.get("sources", [])}
        
    except Exception as raw_sys_err:
        # ─── TOOL ERROR HANDLING ───
        return {
            "is_error": True,
            "error_type": "SYSTEM_EXCEPTION",
            "message": f"Low-Level Critical Exception in RAG vector layer: {str(raw_sys_err)}"
        }


def create_support_ticket(title: str, priority: str) -> Dict[str, Any]:
    """Tool: Registers official help desk issues for operational staff triage."""
    # ─── TOOL INPUT VALIDATION ───
    if priority.title() not in ["Low", "Medium", "High"]:
        return {
            "is_error": True,
            "error_type": "VALIDATION_ERROR",
            "message": f"Malformed Tool Input: Priority '{priority}' is invalid. Options are Low, Medium, or High."
        }
        
    return {
        "is_error": False,
        "ticket_id": "TICKET-2026-NEXUS",
        "status": "QUEUED",
        "assigned_team": "EXPERT_HUMAN_DESK"
    }
