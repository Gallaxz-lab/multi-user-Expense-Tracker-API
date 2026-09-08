import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores.azuresearch import AzureSearch as AzureAISearch
from langchain_core.documents import Document
from app.config import settings

CACHE_DIR = "/tmp/rag_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

embeddings_engine = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.GEMINI_API_KEY
)

def get_azure_search_vector_store() -> AzureAISearch:
    """Connects to Azure AI Search using standard native schemas to prevent upload clashes."""
    return AzureAISearch(
        azure_search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
        azure_search_key=settings.AZURE_SEARCH_API_KEY,
        index_name=settings.AZURE_SEARCH_INDEX_NAME,
        embedding_function=embeddings_engine
    )

def add_docs_to_langchain_retrievers(documents: List[Document]):
    """Pushes vectors into the cloud index safely across all workers."""
    if not documents:
        return

    print(f"📡 Azure AI Search: Pushing {len(documents)} shards with standard structures...")
    vector_store = get_azure_search_vector_store()
    vector_store.add_documents(documents)
    print("✅ Indexing successful: Document shards successfully written to Azure.")

def clear_all_langchain_retrievers():
    """Securely purges your cloud index records."""
    try:
        vector_store = get_azure_search_vector_store()
        vector_store.delete_collection()
        print("✅ Success: Azure AI Search index reset.")
    except Exception as e:
        print(f"⚠️ Reset Warning: {str(e)}")
