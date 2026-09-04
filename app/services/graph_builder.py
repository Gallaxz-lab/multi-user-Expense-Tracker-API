from langgraph.graph import StateGraph, END
from app.schemas.support_state import SupportRouterState
from app.services.support_graph import (
    classify_intent_node,
    generate_general_response_node,
    execute_rag_support_node,
    route_to_human_desk_node,
    choose_next_node_conditional
)

workflow_builder = StateGraph(SupportRouterState)
workflow_builder.add_node("intent_classifier", classify_intent_node)
workflow_builder.add_node("general_responder", generate_general_response_node)
workflow_builder.add_node("rag_assistant", execute_rag_support_node)
workflow_builder.add_node("human_escalator", route_to_human_desk_node)

workflow_builder.set_entry_point("intent_classifier")


workflow_builder.add_conditional_edges(
    "intent_classifier",
    choose_next_node_conditional,
    {
        "execute_general_path": "general_responder",
        "execute_rag_path": "rag_assistant",
        "execute_human_path": "human_escalator"
    }
)

workflow_builder.add_edge("general_responder", END)
workflow_builder.add_edge("rag_assistant", END)
workflow_builder.add_edge("human_escalator", END)

compiled_support_graph = workflow_builder.compile()
