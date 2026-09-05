from typing import Dict, Any

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
    """Tool: Searches verified document snippets for compliance rules."""
    query_lower = query.lower()
    
    if "meal" in query_lower or "food" in query_lower:
        return {"success": True, "context": "Clause 1.A: Domestic meal caps are restricted to $55.00 USD per individual."}
    if "hardware" in query_lower or "engineering" in query_lower:
        return {"success": True, "context": "Clause 2.B: System registration identifier token matches code id-9904."}
        
    return {"success": False, "context": "No matching documentation snippets found in data arrays."}


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
