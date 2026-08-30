import os
import re
from typing import List, Dict, Any

TOPIC_MAP = {
    "employee_handbook.txt": "HR Policy",
    "expense_guidelines.txt": "Finance",
    "building_safety.txt": "Facilities",
    "it_support.txt": "IT Support",
    "software_license.txt": "Legal",
}

def load_and_chunk_documents() -> List[Dict[str, Any]]:
    """[DOCUMENT -> EXTRACT -> CHUNK] Parses local text assets into overlapping text chunks."""
    knowledge_collection = []
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(os.path.dirname(current_dir))
    docs_folder = os.path.join(root_dir, "knowledge_docs")
    
    if not os.path.exists(docs_folder):
        print(f"⚠️ Warning: knowledge_docs folder not found at: {docs_folder}")
        return []
        
    doc_id = -1
    for file_name in sorted(os.listdir(docs_folder)):
        if file_name.endswith(".txt"):
            file_path = os.path.join(docs_folder, file_name)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
 
            # Smart Sentence/Line Chunking
            raw_lines = content.split("\n")
            lines = [line.strip() for line in raw_lines if line.strip()]
            
            # Group lines into chunks with sliding overlap so context isn't lost
            chunk_size = 2  # merge 2 lines together
            overlap = 1    # overlap by 1 line
            
            for i in range(0, len(lines), chunk_size - overlap):
                chunk_lines = lines[i:i + chunk_size]
                chunk_text = " ".join(chunk_lines)
                if not chunk_text:
                    continue
                    
                knowledge_collection.append({
                    "id": doc_id,
                    "text": chunk_text,
                    "category": TOPIC_MAP.get(file_name, "General Documentation"),
                    "source_file": file_name,
                    "last_updated": f"{file_name}#chunk_{i}"
                })
                doc_id -= 1
            
    print(f"📊 Extraction Complete: Generated {len(knowledge_collection)} overlapping text nodes.")
    return knowledge_collection
