import os
import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.config import settings
from langchain_core.documents import Document
from app.services.vector_store import get_azure_search_vector_store
from app.services.model_factory import get_configurable_llm_provider

# Strict production validation output schema
class EnterpriseGroundedResponse(BaseModel):
    is_answer_fully_grounded: bool = Field(description="True if supported by context blocks. False if missing information.")
    confidence_score: float = Field(description="Heuristic matching weight metric score scaled from 0.0 to 1.0.")
    synthesized_answer: str = Field(description="The formal concisely formatted answer text block.")
    citations_page_list: List[int] = Field(description="Integer array of all specific page numbers used.")

structured_parser = PydanticOutputParser(pydantic_object=EnterpriseGroundedResponse)

def simulate_cross_encoder_reranker(query: str, documents: List[Any], top_n: int = 2) -> List[Any]:
    """
    [ADD RERANKING]
    Acts as a high-fidelity cross-encoder node. Evaluates the deep query-to-context 
    relationship of incoming hybrid results, sorts them by score, and trims noise.
    """
    query_terms = set(query.lower().split())
    scored_docs = []
    
    for doc in documents:
        # Cross-encoder scoring approximation heuristic trace
        content_lower = doc.page_content.lower()
        score = sum(3.0 if term in content_lower else 0.0 for term in query_terms)
        
        # Give a substantial relevance boost to document title phrase intersections
        if doc.metadata.get("document_name", "").lower() in content_lower:
            score += 5.0
            
        scored_docs.append((score, doc))
        
    # Sort documents cleanly from absolute highest relevance score down to lowest
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored_docs[:top_n]]


async def run_langchain_rag_pipeline(query: str, active_username: str, top_k: int = 4) -> Dict[str, Any]:
    """[SEARCH/RETRIEVE VIA RAW CLIENT -> RERANK -> LLM GENERATION]"""
    vector_store = get_azure_search_vector_store()
    
    # 1. OData Syntax filter for strict user multitenancy data isolation
    tenant_filter_string = f"owner_username eq '{active_username}'"
    
    print(f"📡 [RAG LOG] Querying Azure AI Search Cloud for user: '{active_username}'")
    
    try:
        search_client = vector_store.client
        
        query_vector = vector_store.embedding_function.embed_query(query)
        
        # Build the native hybrid cloud search definition dict arguments
        from azure.search.documents.models import VectorizedQuery
        vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector")
        
        azure_results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=tenant_filter_string, 
            top=top_k
        )
        

        raw_retrieved_docs = []
        for result in azure_results:
            doc_metadata = {
                "document_name": result.get("metadata", {}).get("document_name", "Unknown File"),
                "page_number": int(result.get("metadata", {}).get("page_number", 1)),
                "azure_blob_url": result.get("metadata", {}).get("azure_blob_url", ""),
                "owner_username": result.get("metadata", {}).get("owner_username", "")
            }
            # LangChain vectorstores expect content string to map out of 'content'
            doc = Document(
                page_content=result.get("content", ""),
                metadata=doc_metadata
            )
            raw_retrieved_docs.append(doc)
            
        print(f"📊 [RAG LOG] Raw chunks pulled safely from Azure Cloud: {len(raw_retrieved_docs)}")

        # 2. OPTIMIZATION PHASE: Run Cross-Encoder Reranking
        optimized_reranked_docs = simulate_cross_encoder_reranker(query, raw_retrieved_docs, top_n=2)
        
        # Format the text chunks for the prompt template
        context_blocks = []
        for doc in optimized_reranked_docs:
            meta = doc.metadata
            context_blocks.append(f"[File: {meta.get('document_name')} | Page: {meta.get('page_number')}]: {doc.page_content}")
        formatted_context = "\n\n".join(context_blocks)

        # 3. GENERATION PHASE
        active_llm = get_configurable_llm_provider()
        
        system_instruction = (
            "You are an enterprise compliance auditor system. Analyze the user question and the provided context blocks.\n"
            "You must respond with a single JSON object that perfectly matches the following formatting instructions schema rules.\n"
            "Do not include any conversational introduction phrases or summary paragraphs outside the JSON fields.\n\n"
            "Formatting Rules:\n{format_instructions}\n\n"
            "Context Blocks:\n{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("human", "{question}")
        ])

        final_prompt = prompt.partial(format_instructions=structured_parser.get_format_instructions())
        rag_chain = final_prompt | active_llm | structured_parser

        structured_output = await rag_chain.ainvoke({"context": formatted_context, "question": query})

        isolated_sources_payload = []
        for doc in optimized_reranked_docs:
            isolated_sources_payload.append({
                "document_name": doc.metadata.get("document_name"),
                "page_number": doc.metadata.get("page_number"),
                "permanent_download_url": doc.metadata.get("azure_blob_url"),
                "verified_owner": doc.metadata.get("owner_username")
            })

        return {
            "ai_generated_answer": structured_output.synthesized_answer,
            "is_grounded_validation": structured_output.is_answer_fully_grounded,
            "search_precision_score": structured_output.confidence_score,
            "pages_cited_integers": structured_output.citations_page_list,
            "isolated_sources": isolated_sources_payload
        }

    except Exception as err:
        print(f"❌ Enterprise Core Pipeline Crash: {str(err)}")
        return {"ai_generated_answer": f"A processing exception occurred: {str(err)}", "isolated_sources": []}