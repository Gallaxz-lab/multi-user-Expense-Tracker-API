import os
import pickle
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from app.config import settings

# Unified shared file path markers inside your container
CACHE_DIR = "/tmp/rag_cache"
VECTOR_STORE_PATH = os.path.join(CACHE_DIR, "vector_store.json")
BM25_STORE_PATH = os.path.join(CACHE_DIR, "bm25_store.pkl")

os.makedirs(CACHE_DIR, exist_ok=True)

embeddings_engine = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=settings.GEMINI_API_KEY
)

def get_vector_store() -> Chroma:
    """Loads or creates a real on-disk Chroma vector database index."""
    return Chroma(
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings_engine
    )

def get_keyword_retriever() -> BM25Retriever:
    """Loads the shared full-text BM25 index from file storage across worker pipelines."""
    if os.path.exists(BM25_STORE_PATH):
        try:
            with open(BM25_STORE_PATH, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"⚠️ BM25 file load failed: {str(e)}")
    return None

def add_docs_to_langchain_retrievers(documents: List[Document]):
    """[STORE & PERSIST] Records elements across multi-worker file architectures natively."""
    if not documents:
        return
    vector_store = get_vector_store()
    vector_store.add_documents(documents)
    bm25_retriever = BM25Retriever.from_documents(documents)
    with open(BM25_STORE_PATH, "wb") as f:
        pickle.dump(bm25_retriever, f)
        
    print(f"✅ LangChain indices successfully written to production workspace disk coordinates.")

def clear_all_langchain_retrievers():
    """[RESET ENGINE STORAGE] Purges local directory trees completely."""
    if os.path.exists(BM25_STORE_PATH):
        os.remove(BM25_STORE_PATH)
    vector_store = get_vector_store()
    try:
        vector_store.delete_collection()
    except Exception:
        pass
    print("🧹 Production RAG cache tables reset completely.")