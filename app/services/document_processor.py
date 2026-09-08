import os
import tempfile
from typing import List
from azure.storage.blob import BlobServiceClient
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.config import settings

blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(settings.AZURE_STORAGE_CONTAINER_NAME)

try:
    container_client.create_container()
except Exception:
    pass

def process_uploaded_pdf_to_langchain_docs(file_bytes: bytes, filename: str, uploader_username: str) -> List[Document]:
    """[INCOMING PDF BINARY STREAM -> AZURE STORAGE LAKE BACKUP -> SEMANTIC METADATA CHUNKING]"""
    
    # 1. Permanent Enterprise Storage Backup Pipeline Pass
    blob_client = container_client.get_blob_client(filename)
    blob_client.upload_blob(file_bytes, overwrite=True)
    print(f"☁️ Azure Storage: Preserved secure backup link for '{filename}'.")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
        temp_pdf.write(file_bytes)
        temp_pdf_path = temp_pdf.name

    try:
        loader = PyPDFLoader(temp_pdf_path)
        raw_documents = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        split_docs = text_splitter.split_documents(raw_documents)

        # Embedding explicit tracking variables to power downstream server query filtering
        for idx, doc in enumerate(split_docs):
            doc.metadata["document_name"] = filename
            doc.metadata["chunk_id"] = idx
            doc.metadata["azure_blob_url"] = blob_client.url
            doc.metadata["page_number"] = int(doc.metadata.get("page", 0)) + 1
            
            # Metadata Filter Hook: Secures documents by pinning them to a specific user
            doc.metadata["owner_username"] = uploader_username

        print(f"📊 Metadata Indexer: Formatted {len(split_docs)} isolated context shards for user '{uploader_username}'.")
        return split_docs

    finally:
        if os.path.exists(temp_pdf_path):
            os.remove(temp_pdf_path)
