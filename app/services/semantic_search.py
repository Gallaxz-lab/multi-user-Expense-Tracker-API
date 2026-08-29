import os
import numpy as np
from google import genai
from typing import List, Dict, Any

from app.config import settings

# Initialize the official Google GenAI client
ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# Map filenames directly to their high-level topic categories
TOPIC_MAP = {
    "employee_handbook.txt": "HR Policy",
    "expense_guidelines.txt": "Finance",
    "building_safety.txt": "Facilities",
    "it_support.txt": "IT Support",
    "software_license.txt": "Legal",
}

def load_knowledge_base_from_disk() -> List[Dict[str, Any]]:
    """Dynamically parses local text assets into structural context maps."""
    knowledge_collection = []
    
    # Path inside Docker workspace (/workspace/knowledge_docs)
    docs_folder = os.path.join(os.getcwd(), "knowledge_docs")
    
    # Fallback to local hardcoded values if the directory is missing (safeguard)
    if not os.path.exists(docs_folder):
        print("⚠️ Warning: knowledge_docs folder not found on disk. Initializing empty.")
        return []
        
    doc_id = -1
    for file_name in sorted(os.listdir(docs_folder)):
        if file_name.endswith(".txt"):
            file_path = os.path.join(docs_folder, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                
            knowledge_collection.append({
                "id": doc_id,
                "text": content,
                "category": TOPIC_MAP.get(file_name, "General Documentation"),
                "last_updated": file_name # Using filename as provenance source data tracking
            })
            doc_id -= 1 # Keep IDs negative to stay clear of database entries
            
    print(f"📊 Successfully loaded {len(knowledge_collection)} knowledge files from disk.")
    return knowledge_collection

# Initialize dynamic loading mapping out data parameters
DOCUMENT_KNOWLEDGE_BASE = load_knowledge_base_from_disk()
CACHED_DOCUMENT_EMBEDDINGS: List[np.ndarray] = []

def get_embedding(text: str) -> np.ndarray:
    cleaned_text = text.strip() if text else "Empty text block placeholder node"
    try:
        response = ai_client.models.embed_content(
            model="gemini-embedding-001",
            contents=cleaned_text
        )
        return np.array(response.embeddings[0].values, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"Gemini embedding calculation layer failed: {str(e)}")

def initialize_vector_cache():
    """Generates and caches embeddings for the dynamic collection at app boot time."""
    global DOCUMENT_KNOWLEDGE_BASE
    
    # If the app booted empty, try re-reading disk (useful for docker mounts)
    if not DOCUMENT_KNOWLEDGE_BASE:
        DOCUMENT_KNOWLEDGE_BASE = load_knowledge_base_from_disk()
        
    if not CACHED_DOCUMENT_EMBEDDINGS and DOCUMENT_KNOWLEDGE_BASE:
        print("⏳ Generating vector index array mappings for disk documentation...")
        validated_docs = []
        
        for doc in DOCUMENT_KNOWLEDGE_BASE:
            # 3. Defensive Skip Check: Ignore empty lines or malformed files trying to compromise vector generation
            if not doc["text"].strip():
                print(f"⚠️ Skipping vector compilation for file ID {doc['id']} ({doc['last_updated']}): File contains no extractable text characters.")
                continue
                
            try:
                vector = get_embedding(doc["text"])
                CACHED_DOCUMENT_EMBEDDINGS.append(vector)
                validated_docs.append(doc)
            except Exception as loop_err:
                print(f"❌ Failed to calculate vector array node for text asset: {str(loop_err)}")
                continue
        
        # Override data index list to include only successfully calculated text nodes
        DOCUMENT_KNOWLEDGE_BASE = validated_docs
        print(f"✅ Vector cache initialized. Indexed {len(CACHED_DOCUMENT_EMBEDDINGS)} items successfully.")

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculates the angular closeness of two text embeddings via vector geometry."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def search_unified_knowledge(query: str, db_expenses: List[Any], top_k: int = 3) -> List[Dict[str, Any]]:
    """Merges static document caching indexes with real-time vector conversions of active user data profiles."""
    initialize_vector_cache()
    
    query_vector = get_embedding(query)
    scored_results = []
    
    # ---- PIPELINE PHASE A: Evaluate File-Based Ingested Documentation ----
    for idx, doc_vector in enumerate(CACHED_DOCUMENT_EMBEDDINGS):
        score = cosine_similarity(query_vector, doc_vector)
        scored_results.append({
            "score": round(score, 4),
            "source": "System Documentation",
            "data": DOCUMENT_KNOWLEDGE_BASE[idx]
        })
        
    # ---- PIPELINE PHASE B: Evaluate Real-Time Dynamic SQL Database Records ----
    for expense in db_expenses:
        expense_text = f"Expense description: {expense.description}. Cost: {expense.amount} dollars. Categorized under: {expense.category_rel.name}."
        expense_vector = get_embedding(expense_text)
        score = cosine_similarity(query_vector, expense_vector)
        
        scored_results.append({
            "score": round(score, 4),
            "source": "User Financial Record",
            "data": {
                "id": expense.id,
                "text": f"Spent ${expense.amount} on '{expense.description}'",
                "category": expense.category_rel.name,
                "last_updated": str(expense.date)
            }
        })
        
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]
