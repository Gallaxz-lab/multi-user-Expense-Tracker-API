import asyncio
from google import genai
from google.genai import types
from typing import List, Dict, Any
from app.config import settings
from app.services.vector_store import retrieve_relevant_contexts

ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def run_structured_rag_pipeline(query: str, db_expenses: List[Any], limit: int) -> Dict[str, Any]:
    """[LLM -> ANSWER + SOURCES] Compiles contexts and builds a grounded final answer."""
    
    # 1. Retrieve hybrid data context nodes
    contexts = retrieve_relevant_contexts(query=query, db_expenses=db_expenses, top_k=limit)
    
    # 2. Build explicit clear LLM context formatting blocks
    context_str = ""
    sources_metadata = []
    
    for item in contexts:
        source_name = item["source"]
        text_content = item["data"]["text"]
        score = item["score"]
        
        context_str += f"- [{source_name}] (Match: {score}): {text_content}\n"
        
        # Only return confident references to the user interface response data
        if score >= 0.35:
            sources_metadata.append({
                "score": score,
                "source": source_name,
                "category": item["data"]["category"],
                "text": text_content,
                "last_updated": item["data"]["last_updated"]
            })

    # 3. Formulate strict grounding instruction
    system_instruction = (
        "You are an expert financial policy and transaction analyst for an expense tracking API. "
        "Your task is to answer the user's question using ONLY the provided verified context lines. "
        "If the information is not present, respond with: 'I am sorry, but I do not have access to that information.' "
        "Do not guess or assume data points."
    )
    
    prompt = f"""
    Context Data Blocks:
    {context_str}
    
    User Query: {query}
    
    Synthesize an answer and cite what rule or item matches from the items provided above:
    """

    try:
        response = await ai_client.aio.models.generate_content(
            model='models/gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                system_instruction=system_instruction
            )
        )
        
        return {
            "answer": response.text.strip() if response.text else "No response generated.",
            "sources": sources_metadata
        }
        
    except Exception as e:
        raise RuntimeError(f"RAG Generation Layer crashed: {str(e)}")
