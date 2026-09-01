import json
from google import genai
from google.genai import types
from typing import List, Dict, Any
from app.config import settings
from app.services.vector_store import run_real_keyword_search, run_real_semantic_search

ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

def run_real_hybrid_fusion(query: str, limit: int) -> List[Dict[str, Any]]:
    """Blends primitive keyword matches and vector locations using Reciprocal Rank Fusion."""
    keyword_res = run_real_keyword_search(query, top_k=15)
    semantic_res = run_real_semantic_search(query, top_k=15)
    
    rrf_scores: Dict[str, float] = {}
    item_lookup: Dict[str, Dict[str, Any]] = {}
    K = 60
    
    for rank, item in enumerate(keyword_res):
        cid = item["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (K + (rank + 1)))
        item_lookup[cid] = item

    for rank, item in enumerate(semantic_res):
        cid = item["chunk_id"]
        rrf_scores[cid] = rrf_scores.get(cid, 0.0) + (1.0 / (K + (rank + 1)))
        item_lookup[cid] = item

    fused = []
    for cid, score in rrf_scores.items():
        base = item_lookup[cid]
        fused.append({
            "score": round(score, 5),
            "chunk_id": cid,
            "text": base["text"],
            "metadata": base["metadata"]
        })
    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused[:limit]

async def run_production_reranker(query: str, candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """[RERANK] Employs a true Gemini cross-encoder pass to evaluate real chunk data text."""
    if not candidates:
        return []
    
    evaluation_payload = [{"index": i, "text": c["text"]} for i, c in enumerate(candidates)]
    prompt = f"""
    Evaluate how relevant each text block is to completely answering the user query.
    User Query: "{query}"
    Candidates: {json.dumps(evaluation_payload)}
    Respond strictly in JSON array format matching this pattern: [{{ "index": 0, "relevance_score": 0.95 }}]
    """
    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash', contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0, response_mime_type="application/json")
        )
        scores = json.loads(response.text.strip())
        score_map = {item["index"]: item["relevance_score"] for item in scores}
        
        for idx, item in enumerate(candidates):
            item["score"] = score_map.get(idx, 0.0)
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:top_k]
    except Exception:
        return candidates[:top_k]



async def run_pdf_assistant_pipeline(query: str, top_k: int = 3) -> Dict[str, Any]:
    """[LLM -> ANSWER + SOURCES + DIAGNOSTICS] Complete context tracking engine."""
    
    # 1. Fetch best items using our unified hybrid search logic
    hybrid_candidates = run_real_hybrid_fusion(query, limit=6)
    
    # 2. Filter list down using our Gemini verification tier
    validated_chunks = await run_production_reranker(query, hybrid_candidates, top_k=top_k)
    
    # 3. Format grounded text context blocks
    context_str = ""
    sources_metadata = []
    highest_score = 0.0
    
    for item in validated_chunks:
        meta = item["metadata"]
        score = item["score"]
        if score > highest_score:
            highest_score = score
            
        context_str += f"[Document: {meta['document_name']} | Page: {meta['page_number']}]: {item['text']}\n\n"
        
        sources_metadata.append({
            "document_name": meta["document_name"],
            "page_number": meta["page_number"],
            "chunk_id": meta["chunk_id"],
            "relevance_rank_score": score
        })

    system_instruction = (
        "You are an expert operations analyst. Answer the user's question using ONLY the provided verified context lines. "
        "If the information is not present in the text blocks, respond exactly with: "
        "'I cannot find the answer in the provided documents.' Do not guess or assume data points."
    )
    
    prompt = f"Verified Material:\n{context_str}\n\nUser Question: {query}\n\nFormulate your answer:"

    retrieval_status = "SUCCESS" if validated_chunks else "EMPTY_RETRIEVAL"
    
    try:
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.1, system_instruction=system_instruction)
        )
        
        answer_text = response.text.strip() if response.text else ""
        generation_status = "SUCCESS"
        if "cannot find the answer" in answer_text.lower() or not answer_text:
            generation_status = "FAILED_UNGROUNDED"

        return {
            "answer": answer_text,
            "sources": sources_metadata,
            "diagnostics": {
                "retrieval_status": retrieval_status,
                "generation_status": generation_status,
                "highest_matching_score": highest_score,
                "suggested_issue_root": "BAD_RETRIEVAL" if retrieval_status == "EMPTY_RETRIEVAL" or highest_score < 0.30
                                        else ("BAD_GENERATION" if generation_status == "FAILED_UNGROUNDED" else "NONE"),
                "inspect_retrieved_chunks": validated_chunks
            }
        }
    except Exception as e:
        raise RuntimeError(f"Production generation failed: {str(e)}")
