import re
from typing import Dict, Any
from app.schemas.support_state import SupportRouterState
from app.services import agent_tools

def agent_brain_node(state: SupportRouterState) -> Dict[str, Any]:
    """
    Analyzes the query and current tool results to select the next logical action.
    """
    query = state["user_query"].lower()
    results = state["tool_results"]
    history = state["executed_tools"]
    current_loops = state["loop_count"] + 1
    
    if current_loops > 5:
        return {
            "next_step": "stop",
            "loop_count": current_loops,
            "final_response": "I apologize, but I hit a routing limit trying to resolve this request."
        }

    next_action = "stop"
    
    # Case A: User asks a multi-step query needing customer lookup first
    if "customer" in query or "cust-" in query:
        if "get_customer_info" not in history:
            next_action = "call_customer_tool"
            
    # Case B: User asks about guidelines/rules and we haven't searched documents yet
    if any(w in query for w in ["limit", "policy", "code", "meal", "hardware"]):
        if "search_knowledge_base" not in history:
            next_action = "call_knowledge_tool"
            
    # Case C: Request explicitly requires ticket generation escalation
    if any(w in query for w in ["ticket", "complain", "human", "open", "refund"]):
        if "create_support_ticket" not in history:
            if "CUST-" in state["user_query"].upper() and "get_customer_info" not in history:
                next_action = "call_customer_tool"
            else:
                next_action = "call_ticket_tool"

    return {
        "next_step": next_action,
        "loop_count": current_loops
    }


def execute_tool_node(state: SupportRouterState) -> Dict[str, Any]:
    """
    Executes the chosen tool, extracts arguments, tracks history, and logs error payloads.
    """
    action = state["next_step"]
    query = state["user_query"]
    
    updated_history = list(state["executed_tools"])
    updated_results = dict(state["tool_results"])
    
    if action == "call_customer_tool":
        match = re.search(r"cust-\d+", query.lower())
        cust_id = match.group(0).upper() if match else "INVALID"
        
        tool_output = agent_tools.get_customer_info(cust_id)
        updated_history.append("get_customer_info")
        updated_results["get_customer_info"] = tool_output

    elif action == "call_knowledge_tool":
        tool_output = agent_tools.search_knowledge_base(query)
        updated_history.append("search_knowledge_base")
        updated_results["search_knowledge_base"] = tool_output

    elif action == "call_ticket_tool":
        forced_priority = "INVALID" if "force_error" in query.lower() else "High"
        
        tool_output = agent_tools.create_support_ticket(title=f"Agent Issue: {query[:30]}", priority=forced_priority)
        updated_history.append("create_support_ticket")
        updated_results["create_support_ticket"] = tool_output

    return {
        "executed_tools": updated_history,
        "tool_results": updated_results,
        "next_step": "re_evaluate" 
    }


def final_responder_node(state: SupportRouterState) -> Dict[str, Any]:
    """Compiles all collected tool results into a structured answer."""
    results = state["tool_results"]
    query = state["user_query"]
    
    if not results:
        return {"final_response": f"I processed your generic query directly: '{query}'. No database tools were required."}
        
    reply_segments = ["Agent Assessment Complete:"]
    
    if "get_customer_info" in results:
        res = results["get_customer_info"]
        if "error" in res:
            reply_segments.append(f"⚠️ Account Check Failed: {res['message']}")
        else:
            reply_segments.append(f"👤 Verified Customer {res['name']} [Tier: {res['tier']}, Status: {res['status']}].")
            
    if "search_knowledge_base" in results:
        res = results["search_knowledge_base"]
        reply_segments.append(f"📖 Policy Context Found: {res['context']}")
        
    if "create_support_ticket" in results:
        res = results["create_support_ticket"]
        if "error" in res:
            reply_segments.append(f"❌ Ticket Processing Error: {res['message']}")
        else:
            reply_segments.append(f"🎫 Escalation Complete: Generated ticket ID {res['ticket_id']} successfully placed in {res['queue']}.")

    return {"final_response": "\n".join(reply_segments)}


def route_conditional_edges(state: SupportRouterState) -> str:
    """[CONDITIONAL ROUTING] Branching decision driver evaluating the next step flag."""
    action = state.get("next_step", "stop")
    
    if action == "re_evaluate":
        return "loop_back_to_brain"
    elif action == "stop":
        return "go_to_responder"
    else:
        return "go_to_tool_executor"
