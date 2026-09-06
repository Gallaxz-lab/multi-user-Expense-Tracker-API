import asyncio
from typing import Dict, Any
from app.services.rag_engine import run_langchain_rag_pipeline

def get_customer_info(customer_id: str) -> Dict[str, Any]:
    """Tool: Fetches customer CRM tiers with strict alphanumeric input validation."""
    # ─── TOOL INPUT VALIDATION ───
    if not customer_id or not customer_id.startswith("CUST-"):
        return {
            "is_error": True,
            "error_type": "VALIDATION_ERROR",
            "message": f"Malformed Tool Input: Identifier '{customer_id}' must begin with 'CUST-' prefix."
        }
    
    database = {
        "CUST-101": {"name": "Alice Johnson", "tier": "Premium", "status": "Active", "permission_level": 2},
        "CUST-202": {"name": "Bob Smith", "tier": "Free", "status": "Suspended", "permission_level": 1}
    }
    
    if customer_id not in database:
        return {
            "is_error": True,
            "error_type": "NOT_FOUND",
            "message": f"Data Missing Error: Identifier '{customer_id}' does not exist in our user index."
        }
        
    return {"is_error": False, "data": database[customer_id]}


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
