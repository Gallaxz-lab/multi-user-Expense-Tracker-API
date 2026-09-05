import json
import re
from typing import List, Dict, Any
from app.schemas.support_state import SupportRouterState
from app.services.rag_engine import run_langchain_rag_pipeline


# Initialize the conversational routing decision model (with Local Algorithmic Intent Routing Logic)
def classify_intent_node(state: SupportRouterState) -> Dict[str, Any]:
    """
    [EACH NODE USES/CHANGES STATE] 
    Processes intents entirely locally using regex keyword mapping.
    This protects your free API limits from daily quota exhaustion.
    """
    query = state["user_query"].lower()
    

    human_keywords = ["human", "person", "agent", "supervisor", "billing", "money", "complain", "refund", "support", "help desk"]
    rag_keywords = ["policy", "guideline", "limit", "clause", "rule", "code", "token", "page", "document", "pdf", "allowance"]
    if any(word in query for word in human_keywords):
        intent = "human"
    elif any(word in query for word in rag_keywords):
        intent = "rag"
    else:
        intent = "general"
        
    print(f"🔮 [Local Node: Classify] Mapped user query intent route -> '{intent}'")
    return {"classified_intent": intent}


def generate_general_response_node(state: SupportRouterState) -> Dict[str, Any]:
    """[NODE STAGE] Generates safe customer support replies locally."""
    query = state["user_query"].lower()
    
    if any(word in query for word in ["hello", "hi", "hey", "greetings"]):
        reply = "Hello! Welcome to the AI Support Desk. How can I assist you with your expense tracking operations today?"
    elif any(word in query for word in ["thank", "thanks", "appreciate"]):
        reply = "You are very welcome! Let me know if you need anything else."
    else:
        reply = "I received your query. Please let me know if you need specific details about company policy or require human support assistance."
        
    return {"final_response": reply}


async def execute_rag_support_node(state: SupportRouterState) -> Dict[str, Any]:
    """Hooks directly into your production LangChain FAISS retrieval chain."""
    query = state["user_query"]
    
    # Run the stable LangChain file-backed retriever we built earlier
    rag_payload = await run_langchain_rag_pipeline(query=query, top_k=3)
    
    return {
        "final_response": rag_payload.get("answer"),
        "source_citations": rag_payload.get("sources")
    }


def route_to_human_desk_node(state: SupportRouterState) -> Dict[str, Any]:
    """Simulates support ticket creation workflows for live staff agents."""
    return {
        "final_response": (
            "I have classified your request as requiring expert human assistance. "
            "A high-priority support ticket has been opened for your profile, "
            "and an operations agent will contact you shortly."
        )
    }


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



'''
# Initialize the conversational routing decision model (with a free-tier Google Gemini API key)
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
        
        content_text = ""
        if isinstance(response.content, str):
            content_text = response.content.strip()
        elif isinstance(response.content, list):
            content_text = "".join([str(item) for item in response.content]).strip()
        else:
            content_text = str(response.content).strip()

        if "```" in content_text:
            content_text = content_text.split("```")[1]
            if content_text.startswith("json"):
                content_text = content_text[4:]
        content_text = content_text.strip()

        data = json.loads(content_text)
        intent = data.get("intent", "general")
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
            print("⚠️ 429 Daily Limit Hit. Activating Local Algorithmic Intent Routing Logic...")
            
            if any(w in query for w in ["human", "person", "agent", "supervisor", "billing", "money", "complain", "refund"]):
                intent = "human"
            elif any(w in query for w in ["policy", "guideline", "limit", "clause", "rule", "code", "token", "page", "document"]):
                intent = "rag"
            else:
                intent = "general"
        else:
            intent = "general"
        
    print(f"🔮 [Node: Classify] Mapped user query intent classification route -> '{intent}'")
    return {"classified_intent": intent}


def generate_general_response_node(state: SupportRouterState) -> Dict[str, Any]:
    """Handles basic conversational queries directly without reading PDF assets."""
    query = state["user_query"]
    
    response = routing_llm.invoke([
        SystemMessage(content="You are a helpful customer support agent for an expense tracker. Provide a friendly response."),
        HumanMessage(content=query)
    ])
    
    return {"final_response": response.content.strip()}

'''