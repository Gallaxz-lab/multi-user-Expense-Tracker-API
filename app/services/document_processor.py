import os
import io
from pypdf import PdfReader
from typing import List, Dict, Any

# =====================================================================
# PART 1: PRODUCTION REAL PDF PROCESSING ENGINE
# =====================================================================

def chunk_text_by_words(text: str, chunk_size: int = 150, overlap: int = 30) -> List[str]:
    """Splits text by words using a sliding window for higher granularity than lines."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
    return chunks

def extract_and_chunk_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    """[PDF UPLOAD -> EXTRACT -> BETTER CHUNKING] Extracts pages and tracks metadata."""
    chunks_collection = []
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    
    global_chunk_idx = 0
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text()
        if not page_text or not page_text.strip():
            continue
            
        # Better semantic chunking via word sliding window per page
        page_chunks = chunk_text_by_words(page_text, chunk_size=120, overlap=25)
        
        for chunk_text in page_chunks:
            chunks_collection.append({
                "id": f"{filename}#c{global_chunk_idx}",
                "text": chunk_text,
                "category": "Uploaded PDF Documentation",
                "metadata": {
                    "document_name": filename,
                    "page_number": page_num,
                    "chunk_id": global_chunk_idx
                }
            })
            global_chunk_idx += 1
            
    return chunks_collection


# =====================================================================
# PART 2: METRICS LAB SIMULATION ENGINE
# =====================================================================

# Mock static database collection used strictly by the comparison lab
SIMULATED_PDF_CHUNKS = [
    {"id": "chunk_1", "page": 1, "text": "For overnight hotel stays, corporate lodging travel coverage is capped securely."},
    {"id": "chunk_2", "page": 2, "text": "Itemized dinner restaurant bills must be submitted to the expense log app."},
    {"id": "chunk_3", "page": 3, "text": "Hardware serial asset token matching code id-9904 registered to engineering facilities."},
    {"id": "chunk_4", "page": 4, "text": "General remote work stipend setups require strict manager sign-offs for all staff."}
]

class DocumentProcessorService:
    @staticmethod
    def simulate_keyword_score(query: str, text: str) -> float:
        """Simulates a BM25 Keyword match (exact token counting)."""
        score = 0.0
        query_words = query.lower().split()
        text_lower = text.lower()
        for word in query_words:
            if word in text_lower:
                score += 1.0
        return score

    @staticmethod
    def simulate_semantic_score(query: str, text: str) -> float:
        """Simulates conceptual Vector matching (semantic intent)."""
        concept_mappings = {
            "sleep": ["lodging", "hotel", "stay", "accommodation"],
            "food": ["meal", "dinner", "allowance", "restaurant"],
            "id-9904": ["id-9904", "serial"]
        }
        query_lower = query.lower()
        text_lower = text.lower()
        
        for key, synonyms in concept_mappings.items():
            if key in query_lower:
                if any(syn in text_lower for syn in synonyms):
                    return 0.85
        return 0.10

    @staticmethod
    def simulate_reranker(initial_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simulates a Reranker cross-encoder model layer sorting priority elements."""
        scored_chunks = []
        for chunk in initial_chunks:
            item = chunk.copy()
            if "capped" in item["text"].lower() or "must" in item["text"].lower():
                item["rerank_score"] = 0.95
            else:
                item["rerank_score"] = 0.40
            scored_chunks.append(item)
                
        return sorted(scored_chunks, key=lambda x: x["rerank_score"], reverse=True)
