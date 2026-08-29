import os
import numpy as np
from google import genai
from typing import List, Dict, Any

from app.config import settings

# Initialize the official Google GenAI client
ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

TOPIC_MAP = {
    "employee_handbook.txt": "HR Policy",
    "expense_guidelines.txt": "Finance",
    "building_safety.txt": "Facilities",
    "it_support.txt": "IT Support",
    "software_license.txt": "Legal",
}

def load_knowledge_base_from_disk() -> List[Dict[str, Any]]:
    """Parses local text assets into structural chunked context maps."""
    knowledge_collection = []
    docs_folder = os.path.join(os.getcwd(), "knowledge_docs")
    
    if not os.path.exists(docs_folder):
        print("⚠️ Warning: knowledge_docs folder not found on disk.")
        return []
        
    doc_id = -1
    for file_name in sorted(os.listdir(docs_folder)):
        if file_name.endswith(".txt"):
            file_path = os.path.join(docs_folder, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
            
            # FIX 1: Split large files by double newlines into logical paragraph chunks
            # This prevents dense documents from diluting specific terms like "refund"
            chunks = [c.strip() for c in content.split("\n\n") if c.strip()]
            
            for chunk_idx, chunk in enumerate(chunks):
                knowledge_collection.append({
                    "id": doc_id,
                    "text": chunk,
                    "category": TOPIC_MAP.get(file_name, "General Documentation"),
                    "last_updated": f"{file_name}#chunk{chunk_idx}"
                })
                doc_id -= 1
            
    print(f"📊 Loaded {len(knowledge_collection)} distinct text chunks from disk.")
    return knowledge_collection

DOCUMENT_KNOWLEDGE_BASE = load_knowledge_base_from_disk()
CACHED_DOCUMENT_EMBEDDINGS: List[np.ndarray] = []

def get_embedding(text: str) -> np.ndarray:
    cleaned_text = text.strip() if text else "Empty text block placeholder node"
    try:
        # Utilizing modern text-embedding-004 standard for improved text discrimination
        response = ai_client.models.embed_content(
            model="gemini-embedding-001", 
            contents=cleaned_text
        )
        return np.array(response.embeddings[0].values, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"Gemini embedding calculation layer failed: {str(e)}")

def initialize_vector_cache():
    """Generates and caches embeddings for the documentation collection once."""
    global DOCUMENT_KNOWLEDGE_BASE, CACHED_DOCUMENT_EMBEDDINGS
    
    if not DOCUMENT_KNOWLEDGE_BASE:
        DOCUMENT_KNOWLEDGE_BASE = load_knowledge_base_from_disk()
        
    if not CACHED_DOCUMENT_EMBEDDINGS and DOCUMENT_KNOWLEDGE_BASE:
        print("⏳ Generating vector index array mappings for disk documentation...")
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
        print(f"✅ Vector cache initialized. Indexed {len(CACHED_DOCUMENT_EMBEDDINGS)} chunks.")

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculates the angular closeness of two text embeddings via vector geometry."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def search_unified_knowledge(query: str, db_expenses: List[Any], top_k: int = 3) -> List[Dict[str, Any]]:
    """Merges static document caching indexes with dynamic vector conversions."""
    initialize_vector_cache()
    
    query_vector = get_embedding(query)
    scored_results = []
    
    # ---- PIPELINE PHASE A: Evaluate File-Based Chunks ----
    for idx, doc_vector in enumerate(CACHED_DOCUMENT_EMBEDDINGS):
        score = cosine_similarity(query_vector, doc_vector)
        scored_results.append({
            "score": round(score, 4),
            "source": "System Documentation",
            "data": DOCUMENT_KNOWLEDGE_BASE[idx]
        })
        
    # ---- PIPELINE PHASE B: Evaluate Real-Time SQL Database Records ----
    for expense in db_expenses:
        # FIX 2: Synchronize vector string context exactly with the stored text output
        # If your query looks for "refund" but text says "Spent $0.0 on a cat phrase", similarity will drop.
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
        
    # Sort from closest semantic match to furthest
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]
