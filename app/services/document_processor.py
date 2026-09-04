import os
import tempfile
from typing import List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

def process_uploaded_pdf_to_langchain_docs(file_bytes: bytes, filename: str) -> List[Document]:
    """[LOADING -> SPLITTING] Loads PDF bytes and slices them into semantic chunks."""
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(file_bytes)
        temp_pdf_path = temp_pdf.name

    try:
        loader = PyPDFLoader(temp_pdf_path)
        raw_documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,    
            length_function=len
        )
        
        split_docs = text_splitter.split_documents(raw_documents)

        # Inject unified global tracking identities inside metadata attributes
        for idx, doc in enumerate(split_docs):
            doc.metadata["document_name"] = filename
            doc.metadata["chunk_id"] = idx
            raw_page = doc.metadata.get("page", doc.metadata.get("page_number", 0))
            doc.metadata["page_number"] = int(raw_page) + 1
        print(f"📊 LangChain Ingestion: Sliced '{filename}' into {len(split_docs)} semantic nodes.")
        return split_docs

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)


""""
#this is the previous module that was used for document processing, but now we are using the new one with more features and better performance.


def chunk_text_by_words(text: str, chunk_size: int = 120, overlap: int = 25) -> List[str]:
    "Splits text by words using a sliding window for high granularity retrieval."
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk_words = words[i:i + chunk_size]
        if not chunk_words:
            continue
        chunks.append(" ".join(chunk_words))
    return chunks

def extract_and_chunk_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
    "[PDF UPLOAD -> EXTRACT -> CHUNK] Extracts pages and tracks precise metadata objects."
    chunks_collection = []
    pdf_file = io.BytesIO(file_bytes)
    reader = PdfReader(pdf_file)
    
    global_chunk_idx = 0
    for page_idx, page in enumerate(reader.pages):
        page_num = page_idx + 1
        page_text = page.extract_text()
        if not page_text or not page_text.strip():
            continue
            
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
"""
