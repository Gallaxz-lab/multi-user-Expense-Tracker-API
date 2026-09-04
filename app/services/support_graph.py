import json
from typing import Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.config import settings
from app.schemas.support_state import SupportRouterState
from app.services.rag_engine import run_langchain_rag_pipeline 

# Initialize the conversational routing decision model
routing_llm = ChatGoogleGenerativeAI(
    model="gemini-3.6-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.0
)

# =====================================================================
# NODE 1: INTENT CLASSIFICATION NODE
# =====================================================================
def classify_intent_node(state: SupportRouterState) -> Dict[str, Any]:
    """[EACH NODE USES/CHANGES STATE] Inspects query text and determines the path."""
    query = state["user_query"]
    
    system_instruction = (
        "You are an elite enterprise support router. Analyze the user query and classify it into "
        "exactly ONE of these three intents:\n"
        "1. 'general' - Casual greetings, small talk, or generic platform troubleshooting questions.\n"
        "2. 'rag' - Specific queries asking about company policies, operational guidelines, limits, or document rules.\n"
        "3. 'human' - Explicit requests to speak to a real person, billing complaints, or critical data errors.\n\n"
        "Respond strictly in JSON format matching this pattern: {\"intent\": \"rag\"}"
    )
    
    try:
        response = routing_llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=f"User Query: '{query}'")
        ])
        
        # Parse the structured JSON response cleanly
        data = json.loads(response.content.strip())
        intent = data.get("intent", "general")
    except Exception:
        intent = "general" # Safe fallback classification boundary
        
    print(f"🔮 [Node: Classify] Mapped user query intent classification route -> '{intent}'")
    # Returns only the keys we want to update/change inside the global state
    return {"classified_intent": intent}


# =====================================================================
# NODE 2: GENERAL RESPONSE ENGINE NODE
# =====================================================================
def generate_general_response_node(state: SupportRouterState) -> Dict[str, Any]:
    """Handles basic conversational queries directly without reading PDF assets."""
    query = state["user_query"]
    
    response = routing_llm.invoke([
        SystemMessage(content="You are a helpful customer support agent for an expense tracker. Provide a friendly response."),
        HumanMessage(content=query)
    ])
    
    return {"final_response": response.content.strip()}


# =====================================================================
# NODE 3: KNOWLEDGE ASSISTANT RAG NODE
# =====================================================================
async def execute_rag_support_node(state: SupportRouterState) -> Dict[str, Any]:
    """Hooks directly into your existing production LangChain FAISS retrieval chain."""
    query = state["user_query"]
    
    # Run the exact pipeline we refactored earlier
    rag_payload = await run_langchain_rag_pipeline(query=query, top_k=3)
    
    return {
        "final_response": rag_payload.get("answer"),
        "source_citations": rag_payload.get("sources")
    }


# =====================================================================
# NODE 4: HUMAN SUPPORT TICKET NODES
# =====================================================================
def route_to_human_desk_node(state: SupportRouterState) -> Dict[str, Any]:
    """Simulates support ticket creation workflows for live staff agents."""
    return {
        "final_response": (
            "I have classified your request as requiring expert human assistance. "
            "A high-priority support ticket has been opened for your profile, "
            "and an operations agent will contact you shortly."
        )
    }


# =====================================================================
# CONDITIONAL ROUTING FUNCTION
# =====================================================================
def choose_next_node_conditional(state: SupportRouterState) -> str:
    """
    [CONDITIONAL ROUTING CHOOSES NEXT NODE]
    Evaluates the state's classified intent and dynamically points to the next step.
    """
    intent = state.get("classified_intent", "general")
    
    if intent == "rag":
        return "execute_rag_path"
    elif intent == "human":
        return "execute_human_path"
    else:
        return "execute_general_path"
