import os
import tempfile
from typing import List
from azure.storage.blob import BlobServiceClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings

# Initialize the Azure Blob storage communication client
blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)

# Ensure our target Azure storage container exists in the cloud on startup
try:
    container_client.create_container()
except Exception:
    pass  # Container already exists

def process_uploaded_pdf_to_langchain_docs(file_bytes: bytes, filename: str) -> List[Document]:
    """[LOAD -> COPIES TO AZURE CLOUD -> SPLIT] Streams files to Azure Blob Storage."""
    
    # 1. PERMANENT ENTERPRISE STORAGE: Upload the raw file to an Azure Blob container
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file_bytes, overwrite=True)
    print(f"☁️ Azure Storage: Successfully uploaded and backed up '{filename}' to Blob container.")

    # 2. LOCAL EXTRACTION PROCESSING
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(file_bytes)
        temp_pdf_path = temp_pdf.name

    try:
        loader = PyPDFLoader(temp_pdf_path)
        raw_documents = loader.load()

        # Optimally expanded chunk configurations to prevent text truncation
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        split_docs = text_splitter.split_documents(raw_documents)

        for idx, doc in enumerate(split_docs):
            doc.metadata["document_name"] = filename
            doc.metadata["chunk_id"] = idx
            # Capture the absolute web link pointing to the file inside your Azure storage account
            doc.metadata["azure_blob_url"] = blob_client.url
            raw_page = doc.metadata.get("page", 0)
            doc.metadata["page_number"] = int(raw_page) + 1

        return split_docs

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
