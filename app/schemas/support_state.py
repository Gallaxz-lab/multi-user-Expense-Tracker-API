from typing import TypedDict, Optional, List, Dict, Any

class SupportRouterState(TypedDict):
    user_query: str
    next_step: Optional[str]
    executed_tools: List[str]
    tool_results: Dict[str, Any]
    loop_count: int
    final_response: Optional[str]
