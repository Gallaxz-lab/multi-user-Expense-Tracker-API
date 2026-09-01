import numpy as np
import re
from google import genai
from typing import List, Dict, Any
from rank_bm25 import BM25Okapi
from app.config import settings

ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Global runtime multi-document state caches
PROD_CHUNKS_DB: List[Dict[str, Any]] = []
PROD_EMBEDDINGS_DB: List[np.ndarray] = []
BM25_ENGINE_INSTANCE: BM25Okapi = None

def tokenize_text(text: str) -> List[str]:
    """Splits text strings into normalized word tokens for keyword matching."""
    return re.findall(r'\w+', text.lower())

def get_embedding(text: str) -> np.ndarray:
    """[EMBED] Generates real vectors via the text-embedding-004 standard."""
    cleaned_text = text.strip() if text else "Empty text block placeholder node"
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-001", 
            contents=cleaned_text
        )
        return np.array(response.embeddings[0].values, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"Gemini embedding extraction layer failed: {str(e)}")


def add_uploaded_pdf_to_real_indices(new_chunks: List[Dict[str, Any]]):
    """[STORE & INDEX] Encodes semantic vectors using rate-safe batch operations."""
    global PROD_CHUNKS_DB, PROD_EMBEDDINGS_DB, BM25_ENGINE_INSTANCE
    
    if not new_chunks:
        return
    print(f"⏳ Processing {len(new_chunks)} text blocks via batch embedding configurations...")
    
    # Gemini safely allows up to 100+ strings per call
    BATCH_SIZE = 15
    
    for i in range(0, len(new_chunks), BATCH_SIZE):
        batch_slice = new_chunks[i:i + BATCH_SIZE]
        
        batch_texts = [chunk["text"].strip() if chunk["text"] else "Empty node placeholder" for chunk in batch_slice]

        try:
            response = ai_client.models.embed_content(
                model="gemini-embedding-001", 
                contents=batch_texts
            )
            for idx, embedding_obj in enumerate(response.embeddings):
                vector_array = np.array(embedding_obj.values, dtype=np.float32)
                
                # Append arrays to your active runtime state indices tracking maps
                PROD_EMBEDDINGS_DB.append(vector_array)
                PROD_CHUNKS_DB.append(batch_slice[idx])
                
        except Exception as batch_err:
            print(f"❌ Batch indexing process failed at window block slice {i}: {str(batch_err)}")
            raise RuntimeError(f"Gemini embedding batch layer crashed: {str(batch_err)}")
        
    # Re-build the production BM25 search corpus dynamically across all loaded documents
    tokenized_corpus = [tokenize_text(c["text"]) for c in PROD_CHUNKS_DB]
    BM25_ENGINE_INSTANCE = BM25Okapi(tokenized_corpus)
    print(f"✅ State updated: {len(PROD_CHUNKS_DB)} assets active in memory.")



def run_real_keyword_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    """[RETRIEVE: KEYWORD] Standard Okapi BM25 text match ranking."""
    global PROD_CHUNKS_DB, BM25_ENGINE_INSTANCE
    if not BM25_ENGINE_INSTANCE or not PROD_CHUNKS_DB:
        return []
        
    tokenized_query = tokenize_text(query)
    scores = BM25_ENGINE_INSTANCE.get_scores(tokenized_query)
    
    results = []
    for idx, score in enumerate(scores):
        if score > 0:
            results.append({
                "score": round(float(score), 4),
                "chunk_id": PROD_CHUNKS_DB[idx]["id"],
                "text": PROD_CHUNKS_DB[idx]["text"],
                "metadata": PROD_CHUNKS_DB[idx]["metadata"]
            })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]

def run_real_semantic_search(query: str, top_k: int) -> List[Dict[str, Any]]:
    """[RETRIEVE: SEMANTIC] Standard vector cosine similarity distance matching."""
    global PROD_CHUNKS_DB, PROD_EMBEDDINGS_DB
    if not PROD_EMBEDDINGS_DB:
        return []
        
    query_vector = get_embedding(query)
    results = []
    
    for idx, doc_vector in enumerate(PROD_EMBEDDINGS_DB):
        dot = np.dot(query_vector, doc_vector)
        norm_q = np.linalg.norm(query_vector)
        norm_d = np.linalg.norm(doc_vector)
        score = float(dot / (norm_q * norm_d)) if norm_q and norm_d else 0.0
        
        results.append({
            "score": round(score, 4),
            "chunk_id": PROD_CHUNKS_DB[idx]["id"],
            "text": PROD_CHUNKS_DB[idx]["text"],
            "metadata": PROD_CHUNKS_DB[idx]["metadata"]
        })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
