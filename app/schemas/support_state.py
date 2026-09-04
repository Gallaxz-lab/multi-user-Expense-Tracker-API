from typing import TypedDict, Optional, List, Dict, Any

class SupportRouterState(TypedDict):
    """
    [STATE STORES USER DATA]
    The absolute data schema passed sequentially across every active graph node.
    """
    user_query: str                  # The incoming user question input text string
    classified_intent: Optional[str] # The semantic route decision (e.g., 'general', 'rag', 'human')
    final_response: Optional[str]    # The final textual response payload generated for the user
    source_citations: Optional[List[Dict[str, Any]]] # Extracted document citation markers if RAG was run