import numpy as np
from google import genai
from typing import List, Dict, Any
from app.config import settings

ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Dynamic global vector storage index
KNOWLEDGE_BASE_STORE: List[Dict[str, Any]] = []
VECTOR_EMBEDDING_STORE: List[np.ndarray] = []

def get_embedding(text: str) -> np.ndarray:
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-001", 
            contents=text.strip() if text else "Empty placeholder"
        )
        return np.array(response.embeddings[0].values, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"Embedding failed: {str(e)}")

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return float(dot_product / (norm_v1 * norm_v2)) if norm_v1 and norm_v2 else 0.0

def add_chunks_to_vector_store(chunks: List[Dict[str, Any]]):
    """Appends incoming runtime chunks and computes their embeddings into memory."""
    global KNOWLEDGE_BASE_STORE, VECTOR_EMBEDDING_STORE
    for chunk in chunks:
        vector = get_embedding(chunk["text"])
        VECTOR_EMBEDDING_STORE.append(vector)
        KNOWLEDGE_BASE_STORE.append(chunk)

def query_vector_store(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """[TOP-K RETRIEVAL] Locates matching contexts with precise diagnostics scores."""
    if not VECTOR_EMBEDDING_STORE:
        return []
        
    query_vector = get_embedding(query)
    scored_results = []
    
    for idx, doc_vector in enumerate(VECTOR_EMBEDDING_STORE):
        score = cosine_similarity(query_vector, doc_vector)
        scored_results.append({
            "score": round(score, 4),
            "chunk_id": KNOWLEDGE_BASE_STORE[idx]["id"],
            "text": KNOWLEDGE_BASE_STORE[idx]["text"],
            "metadata": KNOWLEDGE_BASE_STORE[idx]["metadata"]
        })
        
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]
