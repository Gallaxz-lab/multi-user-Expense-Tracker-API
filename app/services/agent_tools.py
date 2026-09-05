import asyncio
from typing import Dict, Any
from app.services.rag_engine import run_langchain_rag_pipeline

def get_customer_info(customer_id: str) -> Dict[str, Any]:
    """Tool: Fetches account tier and active permissions for validation checks."""
    if not customer_id or not customer_id.startswith("CUST-"):
        return {"error": "INVALID_ID_FORMAT", "message": "Customer ID must begin with prefix 'CUST-'."}
    
    database = {
        "CUST-101": {"name": "Alice Johnson", "tier": "Premium", "status": "Active"},
        "CUST-202": {"name": "Bob Smith", "tier": "Free", "status": "Suspended"}
    }
    
    return database.get(customer_id, {"error": "NOT_FOUND", "message": "Customer record missing."})


def search_knowledge_base(query: str) -> Dict[str, Any]:
    """
    Tool: Queries your live production LangChain FAISS + BM25 retriever index.
    """
    print(f"🔍 [Tool: Knowledge Base] Querying live FAISS indices for: '{query}'")
    try:
        rag_payload = asyncio.run(run_langchain_rag_pipeline(query=query, top_k=2))
        answer = rag_payload.get("answer", "")
        
        if "cannot find the answer" in answer.lower() or not answer.strip():
            return {
                "success": False, 
                "context": "No authoritative matching corporate documentation guidelines located for this query."
            }
            
        return {
            "success": True,
            "context": answer,
            "sources": rag_payload.get("sources", [])
        }
        
    except Exception as err:
        return {
            "success": False,
            "context": f"Internal database connector tool extraction error occurred: {str(err)}",
            "sources": []
        }


def create_support_ticket(title: str, priority: str) -> Dict[str, Any]:
    """Tool: Generates a high-priority ticketing desk log row."""
    if priority.lower() not in ["low", "medium", "high"]:
        return {"error": "VALIDATION_FAILED", "message": "Priority settings must match Low, Medium, or High criteria."}
        
    return {
        "success": True, 
        "ticket_id": "TICKET-99482", 
        "status": "OPENED", 
        "queue": "EXPERT_HUMAN_DESK"
    }
