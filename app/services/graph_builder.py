from langgraph.graph import StateGraph, END
from app.schemas.support_state import SupportRouterState
from app.services.support_graph import (
    agent_brain_node,
    execute_tool_node,
    final_responder_node,
    route_conditional_edges
)

# 1. Initialize the StateGraph machine
agent_graph = StateGraph(SupportRouterState)

# 2. Add structural processing nodes
agent_graph.add_node("agent_brain", agent_brain_node)
agent_graph.add_node("tool_executor", execute_tool_node)
agent_graph.add_node("final_responder", final_responder_node)

# 3. Establish graph entrypoint block
agent_graph.set_entry_point("agent_brain")

# 4. Bind conditional edges to support loopback patterns
agent_graph.add_conditional_edges(
    "agent_brain",
    route_conditional_edges,
    {
        "loop_back_to_brain": "agent_brain",
        "go_to_tool_executor": "tool_executor",
        "go_to_responder": "final_responder"
    }
)

# 5. Connect finishing nodes to the graph terminal endpoint
agent_graph.add_edge("tool_executor", "agent_brain") 
agent_graph.add_edge("final_responder", END)

# 6. Compile graph pipeline state workflows cleanly
compiled_support_graph = agent_graph.compile()
