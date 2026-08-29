import numpy as np
from google import genai
from pydantic import BaseModel
from typing import List, Dict, Any

from app.config import settings

# Initialize the official Google GenAI client
ai_client = genai.Client(api_key=settings.GEMINI_API_KEY)

# 1. Concrete Knowledge base data collection (The stored documents with metadata)
DOCUMENT_KNOWLEDGE_BASE = [
    {
        "id": 1,
        "text": "Employees must submit vacation requests through the HR portal at least two weeks before their planned departure date.",
        "category": "HR Policy",
        "last_updated": "2026-01-15"
    },
    {
        "id": 2,
        "text": "All medical reimbursement claims require an attached digitized receipt and must be submitted within 30 days of the clinic visit.",
        "category": "Finance",
        "last_updated": "2026-03-10"
    },
    {
        "id": 3,
        "text": "To reset your corporate password, navigate to security settings, select multi-factor authentications, and trigger the recovery token.",
        "category": "IT Support",
        "last_updated": "2026-05-22"
    },
    {
        "id": 4,
        "text": "The corporate expenditure tracker application allows users to safely catalog transactional categories, amounts, and dates.",
        "category": "Software Docs",
        "last_updated": "2026-08-25"
    }
]

# 2. Local In-Memory Vector Storage Cache
# In a massive app, this is swapped for a database like Pinecone or pgvector, but local array memory is fastest for core mechanics
CACHED_DOCUMENT_EMBEDDINGS: List[np.ndarray] = []

def get_embedding(text: str) -> np.ndarray:
    """Invokes Google Gemini to generate high-density semantic vector coordinates for text."""
    try:
        response = ai_client.models.embed_content(
            model="text-embedding-004",  # Google's premier text embedding vector model tier
            contents=text
        )
        # Extract the flat numerical array list and cast it as a high-speed numpy float vector
        return np.array(response.embeddings[0].values, dtype=np.float32)
    except Exception as e:
        raise RuntimeError(f"Gemini embedding calculation layer failed: {str(e)}")

def initialize_vector_cache():
    """Generates and caches embeddings for the entire document collection at app boot time."""
    global CACHED_DOCUMENT_EMBEDDINGS
    if not CACHED_DOCUMENT_EMBEDDINGS:
        print("⏳ Generating vector index array mappings for knowledge base documents...")
        for doc in DOCUMENT_KNOWLEDGE_BASE:
            vector = get_embedding(doc["text"])
            CACHED_DOCUMENT_EMBEDDINGS.append(vector)
        print(f"✅ Vector index mapping complete. Cached {len(CACHED_DOCUMENT_EMBEDDINGS)} items.")

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """Calculates the angular closeness of two text embeddings via vector geometry."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return float(dot_product / (norm_v1 * norm_v2))

def search_knowledge_base(query: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Converts a user search query into vector space and returns the closest data matches."""
    # Ensure our vector storage is populated
    initialize_vector_cache()
    
    # Calculate coordinate vector for the user query string
    query_vector = get_embedding(query)
    
    scored_results = []
    # Loop and cross-examine the similarity score of every stored document
    for idx, doc_vector in enumerate(CACHED_DOCUMENT_EMBEDDINGS):
        score = cosine_similarity(query_vector, doc_vector)
        scored_results.append({
            "score": round(score, 4),
            "document": DOCUMENT_KNOWLEDGE_BASE[idx]
        })
        
    # Sort results by closest match score descending and limit output to top_k matching elements
    scored_results.sort(key=lambda x: x["score"], reverse=True)
    return scored_results[:top_k]
