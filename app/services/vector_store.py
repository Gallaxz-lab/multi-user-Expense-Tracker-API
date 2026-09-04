import os
import pickle
from typing import List
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from app.config import settings

CACHE_DIR = "/tmp/rag_cache"
FAISS_DIR = os.path.join(CACHE_DIR, "faiss_index")
BM25_STORE_PATH = os.path.join(CACHE_DIR, "bm25_store.pkl")


os.makedirs(CACHE_DIR, exist_ok=True)


embeddings_engine = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=settings.GEMINI_API_KEY
)

def get_vector_store() -> FAISS:
    """Loads the shared file-backed FAISS index from disk across worker processes."""
    if os.path.exists(os.path.join(FAISS_DIR, "index.faiss")):
        try:
            store = FAISS.load_local(FAISS_DIR, embeddings_engine, allow_dangerous_deserialization=True)
            print("💾 Successfully loaded active FAISS vector store from shared disk.")
            return store
        except Exception as e:
            print(f"⚠️ FAISS file load failed, initializing fallback: {str(e)}")
    return None

def get_keyword_retriever() -> BM25Retriever:
    """Loads the shared full-text BM25 index from file storage across worker pipelines."""
    if os.path.exists(BM25_STORE_PATH):
        try:
            with open(BM25_STORE_PATH, "rb") as f:
                print("💾 Successfully loaded active BM25 retriever from shared disk.")
                return pickle.load(f)
        except Exception as e:
            print(f"⚠️ BM25 file load failed: {str(e)}")
    return None

def add_docs_to_langchain_retrievers(documents: List[Document]):
    """[STORE & PERSIST] Serializes indices onto shared file coordinates natively."""
    if not documents:
        return

    # 1. Update and serialize the FAISS Vector Database to disk
    vector_store = get_vector_store()
    if vector_store:
        vector_store.add_documents(documents)
    else:
        vector_store = FAISS.from_documents(documents, embeddings_engine)
    vector_store.save_local(FAISS_DIR)

    # 2. Update and serialize the BM25 index maps to disk
    bm25_retriever = BM25Retriever.from_documents(documents)
    with open(BM25_STORE_PATH, "wb") as f:
        pickle.dump(bm25_retriever, f)
        
    print(f"✅ LangChain indices successfully written to production workspace disk coordinates.")

def clear_all_langchain_retrievers():
    """[RESET ENGINE STORAGE] Clears all saved index files entirely from local disk storage."""
    if os.path.exists(BM25_STORE_PATH):
        os.remove(BM25_STORE_PATH)
        
    # Remove FAISS local files cleanly
    for filename in ["index.faiss", "index.pkl"]:
        path = os.path.join(FAISS_DIR, filename)
        if os.path.exists(path):
            os.remove(path)
            
    print("🧹 Production FAISS and BM25 RAG cache tables reset completely.")
