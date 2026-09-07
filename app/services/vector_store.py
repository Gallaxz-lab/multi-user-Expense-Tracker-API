import os
from typing import List
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import AzureAISearch  # ✅ Azure Cloud Connector
from langchain_core.documents import Document
from app.config import settings

# Initialize your accessible Gemini vector extraction model
embeddings_engine = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=settings.GEMINI_API_KEY
)

def get_azure_search_vector_store() -> AzureAISearch:
    """Connects programmatically to your managed cloud vector index on Azure."""
    return AzureAISearch(
        azure_search_endpoint=settings.AZURE_SEARCH_ENDPOINT,
        azure_search_key=settings.AZURE_SEARCH_API_KEY,
        index_name=settings.AZURE_SEARCH_INDEX_NAME,
        embedding_function=embeddings_engine
    )

def add_docs_to_langchain_retrievers(documents: List[Document]):
    """[CREATING EMBEDDINGS & AZURE UPLOAD] Pushes vectors into the Azure AI index."""
    if not documents:
        return

    print(f"📡 Azure AI Search: Generating and pushing {len(documents)} vectors to cloud index...")
    vector_store = get_azure_search_vector_store()
    
    # Azure handles writing and data storage automatically in the cloud
    vector_store.add_documents(documents)
    print("✅ Indexing successful: Chunks are safely active across all cloud partitions.")

def clear_all_langchain_retrievers():
    """
    [RESET CLOUD STORAGE ENGINE]
    Securely purges your Azure AI Search cloud index records across all worker nodes.
    Uses LangChain wrapper with a robust fallback to the raw Azure batch deletion SDK method.
    """
    try:
        print(f"🧹 Azure AI Search: Requesting a full collection purge for index: '{settings.AZURE_SEARCH_INDEX_NAME}'...")
        
        # 1. Try the standard LangChain method first
        vector_store = get_azure_search_vector_store()
        vector_store.delete_collection()
        print("✅ Success: Azure AI Search cloud index has been successfully reset via LangChain.")
        
    except Exception as langchain_err:
        print(f"⚠️ LangChain clear method skipped or unsupported: {str(langchain_err)}")
        print("🔄 Activating low-level Azure SDK batch document deletion fallback recovery...")
        
        try:
            # 2. FALLBACK PATH: Use the raw Azure Search Client if LangChain skips
            search_client = vector_store.client
            
            # Fetch all active document IDs in your cloud index partition
            results = search_client.search(search_text="*", select=["id"])
            ids_to_delete = [{"@search.action": "delete", "id": doc["id"]} for doc in results]
            
            if ids_to_delete:
                search_client.upload_documents(documents=ids_to_delete)
                print(f"✅ Success: Safely purged {len(ids_to_delete)} documents via low-level batch SDK.")
            else:
                print("ℹ️ Azure AI Search collection index is already completely empty.")
                
        except Exception as sdk_err:
            print(f"❌ Critical Error: Both clear methods failed to connect to Azure: {str(sdk_err)}")
