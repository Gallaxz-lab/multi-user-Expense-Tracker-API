from google import genai
from google.genai import types
from typing import List, Dict, Any
from app.config import settings
from app.services.vector_store import query_vector_store

ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

async def run_pdf_assistant_pipeline(query: str, top_k: int) -> Dict[str, Any]:
    """[RETRIEVE -> LLM -> ANSWER + SOURCES + INSPECTION]"""
    # 1. Retrieve the top candidates matching vector similarity
    retrieved_chunks = query_vector_store(query=query, top_k=top_k)
    
    # 2. Structure context strings for the model
    context_str = ""
    for item in retrieved_chunks:
        meta = item["metadata"]
        context_str += f"[Doc: {meta['document_name']} | Page: {meta['page_number']} | Score: {item['score']}]: {item['text']}\n\n"

    system_instruction = (
        "You are a strict technical document assistant. Answer the user's question using ONLY the provided text blocks. "
        "If the answer cannot be confidently verified directly from the context text blocks, state explicitly: "
        "'I cannot find the answer in the provided documents.' Do not make up facts."
    )

    prompt = f"Context Material:\n{context_str}\n\nUser Question: {query}\n\nProvide your grounded response:"

    # Determine if retrieval was empty or weak before sending to LLM
    highest_score = retrieved_chunks[0]["score"] if retrieved_chunks else 0.0
    retrieval_status = "SUCCESS" if highest_score >= 0.40 else "WEAK_OR_EMPTY_RETRIEVAL"

    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.0,
                system_instruction=system_instruction
            )
        )
        
        answer_text = response.text.strip() if response.text else ""
        
        # 3. Determine potential pipeline bottleneck reasons
        generation_status = "SUCCESS"
        if "cannot find the answer" in answer_text.lower() or not answer_text:
            generation_status = "FAILED_UNGROUNDED"

        return {
            "answer": answer_text,
            "sources": [
                {
                    "document_name": item["metadata"]["document_name"],
                    "page_number": item["metadata"]["page_number"],
                    "chunk_id": item["metadata"]["chunk_id"],
                    "match_confidence_score": item["score"]
                } for item in retrieved_chunks if item["score"] >= 0.30
            ],
            "diagnostics": {
                "retrieval_status": retrieval_status,
                "generation_status": generation_status,
                "highest_matching_score": highest_score,
                "suggested_issue_root": "BAD_RETRIEVAL" if retrieval_status == "WEAK_OR_EMPTY_RETRIEVAL" 
                                        else ("BAD_GENERATION" if generation_status == "FAILED_UNGROUNDED" else "NONE"),
                "inspect_retrieved_chunks": retrieved_chunks  # Allows checking what text went to the LLM
            }
        }
    except Exception as e:
        raise RuntimeError(f"RAG engine error: {str(e)}")
