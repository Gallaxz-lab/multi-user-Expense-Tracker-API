import numpy as np
from google import genai
from typing import List, Dict, Any
from app.config import settings
from app.services.document_processor import load_and_chunk_documents

ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Global memory storage
DOCUMENT_KNOWLEDGE_BASE: List[Dict[str, Any]] = []
CACHED_DOCUMENT_EMBEDDINGS: List[np.ndarray] = []

def get_embedding(text: str) -> np.ndarray:
    """[EMBED] Utilizing text-embedding-004 standard for text discrimination."""
    cleaned_text = text.strip() if text else "Empty text block placeholder node"
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-001", 
            contents=cleaned_text
        )
        return np.array(response.embeddings[0].values, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"Gemini embedding calculation layer failed: {str(e)}")

def initialize_vector_store():
    """[STORE] Generates and caches embeddings for the documentation collection once."""
    global DOCUMENT_KNOWLEDGE_BASE, CACHED_DOCUMENT_EMBEDDINGS
    
    if not DOCUMENT_KNOWLEDGE_BASE:
        DOCUMENT_KNOWLEDGE_BASE = load_and_chunk_documents()
        
    if not CACHED_DOCUMENT_EMBEDDINGS and DOCUMENT_KNOWLEDGE_BASE:
        print("⏳ Generating vector store array index...")
        validated_docs = []
        vectors = []
        
        for doc in DOCUMENT_KNOWLEDGE_BASE:
            try:
                vector = get_embedding(doc["text"])
                vectors.append(vector)
                validated_docs.append(doc)
            except Exception as loop_err:
                print(f"❌ Failed to calculate vector node: {str(loop_err)}")
                continue
        
        CACHED_DOCUMENT_EMBEDDINGS = vectors
        DOCUMENT_KNOWLEDGE_BASE = validated_docs
        print(f"✅ Vector store ready. Indexed {len(CACHED_DOCUMENT_EMBEDDINGS)} chunks.")

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    return float(dot_product / (norm_v1 * norm_v2)) if norm_v1 and norm_v2 else 0.0

def retrieve_relevant_contexts(query: str, db_expenses: List[Any], top_k: int = 4) -> List[Dict[str, Any]]:
    """[RETRIEVE] Searches static vector caches and live database expenses simultaneously."""
    initialize_vector_store()
    
    query_vector = get_embedding(query)
    scored_results = []
    
    # 1. Search documentation vector database
    for idx, doc_vector in enumerate(CACHED_DOCUMENT_EMBEDDINGS):
        score = cosine_similarity(query_vector, doc_vector)
        scored_results.append({
            "score": round(score, 4),
            "source": "System Documentation",
            "data": DOCUMENT_KNOWLEDGE_BASE[idx]
        })
        
    # 2. Convert and search live database context real-time
    for expense in db_expenses:
        structured_text = f"Spent ${expense.amount} on '{expense.description}' [Category: {expense.category_rel.name}]"
        expense_vector = get_embedding(structured_text)
        score = cosine_similarity(query_vector, expense_vector)
        
        scored_results.append({
            "score": round(score, 4),
            "source": "User Financial Record",
            "data": {
                "id": expense.id,
                "text": structured_text,
                "category": expense.category_rel.name,
                "last_updated": str(expense.date)
            }
        })
        
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]
