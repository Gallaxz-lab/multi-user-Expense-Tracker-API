import os
import io
from pypdf import PdfReader
from typing import List, Dict, Any

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
