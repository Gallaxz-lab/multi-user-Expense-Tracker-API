import re
from typing import Dict, Any, List
from app.schemas.support_state import SupportRouterState
from app.services import agent_tools

def agent_brain_node(state: SupportRouterState) -> Dict[str, Any]:
    query = state["user_query"].lower()
    history = state["executed_tools"]
    error_logs = state["tool_error_logs"]
    current_loops = state["loop_count"] + 1

    if current_loops > 3: 
        return {"next_step": "escalate", "loop_count": current_loops, "human_escalation_required": True}

    unauthorized_keywords = ["admin password", "delete database", "drop tables"]
    if any(keyword in query for keyword in unauthorized_keywords):
        return {"next_step": "refuse", "security_clearance_blocked": True}

    next_action = "stop"

    if any(w in query for w in ["policy", "guideline", "limit", "clause", "rule", "refund", "meal"]):
        if "search_knowledge_base" not in history:
            next_action = "call_knowledge_tool"
            
    if any(w in query for w in ["account", "profile", "my tier", "who am i", "my information"]):
        if "get_customer_info" not in history:
            next_action = "call_customer_tool"

    if any(w in query for w in ["ticket", "open", "solve", "escalate", "human"]):
        if "create_support_ticket" not in history:
            next_action = "call_ticket_tool"

    return {"next_step": next_action, "loop_count": current_loops}


def execute_tool_node(state: SupportRouterState) -> Dict[str, Any]:
    action = state["next_step"]
    query = state["user_query"]
    
    updated_history = list(state["executed_tools"])
    updated_results = dict(state["tool_results"])
    updated_error_logs = list(state["tool_error_logs"])
    force_human_trigger = False

    if action == "call_customer_tool":
        from app.services.agent_tools import get_customer_info_authenticated
        output = get_customer_info_authenticated(state["current_user"])
        
        if output.get("is_error"):
            updated_error_logs.append(f"call_customer_tool_error: {output['error_type']} - {output['message']}")
        else:
            updated_history.append("get_customer_info")
            updated_results["get_customer_info"] = output["data"]

    elif action == "call_knowledge_tool":
        from app.services.agent_tools import search_knowledge_base
        output = search_knowledge_base(query)
        if output.get("is_error"):
            updated_error_logs.append(f"call_knowledge_tool_error: {output['error_type']} - {output['message']}")
        else:
            updated_history.append("search_knowledge_base")
            updated_results["search_knowledge_base"] = output

    elif action == "call_ticket_tool":
        from app.services.agent_tools import create_support_ticket
        priority_arg = "INVALID_RATING" if "bad_input" in query.lower() else "High"
        output = create_support_ticket(title=f"Support Request: {query[:30]}", priority=priority_arg)
        if output.get("is_error"):
            updated_error_logs.append(f"call_ticket_tool_error: {output['error_type']} - {output['message']}")
            force_human_trigger = True
        else:
            updated_history.append("create_support_ticket")
            updated_results["create_support_ticket"] = output

    return {
        "executed_tools": updated_history,
        "tool_results": updated_results,
        "tool_error_logs": updated_error_logs,
        "human_escalation_required": force_human_trigger or state["human_escalation_required"],
        "next_step": "re_evaluate"
    }
    
    

def final_responder_node(state: SupportRouterState) -> Dict[str, Any]:
    """
    [FALLBACK RESPONSE & HUMAN ESCALATION DESK RESPONSE GENERATOR]
    Builds the final text response based on safety flags, blocks, and escalations.
    """
    query = state["user_query"]
    results = state["tool_results"]
    errors = state["tool_error_logs"]

    # 1. Guardrail Refusal Response
    if state["security_clearance_blocked"]:
        return {
            "final_response": (
                "🛑 Security Access Refusal: Your request asks for operational permissions "
                "outside your clearance boundary metrics. This security incident has been "
                "logged, and system command tokens remain locked."
            )
        }

    # 2. Human Escalation Response Gateway
    if state["human_escalation_required"] or state["next_step"] == "escalate":
        error_summary = f"Caught System Errors: {errors}" if errors else "Max loop iterations threshold reached."
        return {
            "final_response": (
                "🧑‍💻 [HUMAN ESCALATION TRIGGERED] I cannot solve this issue automatically via my "
                f"automated tools framework. Reason: {error_summary}. A live human engineering supervisor "
                "has been requested to take full manual control of this customer communication node."
            )
        }

    # 3. Clean Success / Standard Tool Compilation Output
    reply_segments = ["System Task Resolution Summary:"]
    if "get_customer_info" in results:
        c = results["get_customer_info"]
        reply_segments.append(f" - [CRM Node] Verified user {c['name']} [Tier: {c['tier']}, Status: {c['status']}].")
    if "search_knowledge_base" in results:
        k = results["search_knowledge_base"]
        reply_segments.append(f" - [RAG Node] Policy documentation matches: {k['context']}")
    if "create_support_ticket" in results:
        t = results["create_support_ticket"]
        reply_segments.append(f" - [Ticketing Node] Success! Generated Ticket ID {t['ticket_id']} placed in {t['assigned_team']}.")

    # 4. Fallback Response (If no tools ran but query wasn't blocked/escalated)
    if not results and not errors:
        reply_segments.append(f" - [Fallback Direct Output] Query '{query}' processed directly. No active database tool execution was required.")

    return {"final_response": "\n".join(reply_segments)}


def route_conditional_edges(state: SupportRouterState) -> str:
    """[CONDITIONAL ROUTING] Multi-intent execution driver matching next_step directives."""
    action = state.get("next_step", "stop")
    
    if action == "re_evaluate":
        return "loop_back_to_brain"
    elif action in ["stop", "refuse", "escalate"]:
        return "go_to_responder"
    else:
        return "go_to_tool_executor"
