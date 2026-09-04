import os
import pickle
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import InMemoryVectorStore
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

def get_vector_store() -> InMemoryVectorStore:
    """Loads or initializes the shared vector database store instance from the file system."""
    store = InMemoryVectorStore(embeddings_engine)
    if os.path.exists(VECTOR_STORE_PATH):
        try:
            # InMemoryVectorStore supports native text state file loading
            store = InMemoryVectorStore.load(VECTOR_STORE_PATH, embeddings_engine)
            print("💾 Successfully restored active Vector Store states from shared file cache.")
        except Exception as e:
            print(f"⚠️ Vector store load failed, fallback initialization activated: {str(e)}")
    return store

def get_keyword_retriever() -> BM25Retriever:
    """Loads the shared full-text BM25 index from file storage across worker pipelines."""
    if os.path.exists(BM25_STORE_PATH):
        try:
            with open(BM25_STORE_PATH, "rb") as f:
                retriever = pickle.load(f)
                print("💾 Successfully restored full-text BM25 indices from shared file cache.")
                return retriever
        except Exception as e:
            print(f"⚠️ BM25 load failed: {str(e)}")
    return None

def add_docs_to_langchain_retrievers(documents: List[Document]):
    """[STORE & SERIALIZE] Commits elements across multi-worker file architectures."""
    if not documents:
        return

    vector_store = get_vector_store()
    vector_store.add_documents(documents)
    vector_store.dump(VECTOR_STORE_PATH)

    bm25_retriever = BM25Retriever.from_documents(documents)
    with open(BM25_STORE_PATH, "wb") as f:
        pickle.dump(bm25_retriever, f)
        
    print(f"✅ LangChain indices serialized securely onto internal workspace disk coordinates.")

def clear_all_langchain_retrievers():
    """[RESET STORAGE ENGINE] Securely flushes disk caches and resets worker mappings."""
    for path in [VECTOR_STORE_PATH, BM25_STORE_PATH]:
        if os.path.exists(path):
            os.remove(path)
    print("Clean cache reset completed successfully.")
