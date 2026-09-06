from typing import TypedDict, Optional, List, Dict, Any

class SupportRouterState(TypedDict):
    user_query: str
    current_user: Dict[str, Any]
    next_step: Optional[str]
    executed_tools: List[str]
    tool_results: Dict[str, Any]
    tool_error_logs: List[str]
    loop_count: int
    security_clearance_blocked: bool
    human_escalation_required: bool
    final_response: Optional[str]
    
