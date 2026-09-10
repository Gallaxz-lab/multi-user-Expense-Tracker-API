import time
import traceback
import re
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.documents import Document
from app.config import settings
from app.services.vector_store import get_azure_search_vector_store
from app.services.model_factory import get_configurable_llm_provider

from app.services.observability import (
    generate_request_id,
    estimate_token_count,
    calculate_approximate_cost,
    print_telemetry_trace_report
)

class EnterpriseGroundedResponse(BaseModel):
    is_answer_fully_grounded: bool = Field(description="True if supported by context blocks. False if missing info.")
    confidence_score: float = Field(description="Accuracy weight from 0.0 to 1.0 based on context.")
    synthesized_answer: str = Field(description="The formal concise operational answer text.")
    citations_page_list: List[int] = Field(description="Array of all specific page numbers used.")

structured_parser = PydanticOutputParser(pydantic_object=EnterpriseGroundedResponse)

def simulate_cross_encoder_reranker(query: str, documents: List[Any], top_n: int = 2) -> List[Any]:
    query_terms = set(query.lower().split())
    scored_docs = []
    for doc in documents:
        content_lower = doc.page_content.lower()
        score = sum(3.0 if term in content_lower else 0.0 for term in query_terms)
        if doc.metadata.get("document_name", "").lower() in content_lower:
            score += 5.0
        scored_docs.append((score, doc))
    scored_docs.sort(key=lambda x: x[0], reverse=True)
    return [doc for score, doc in scored_docs[:top_n]]


async def run_langchain_rag_pipeline(query: str, active_username: str, top_k: int = 4) -> Dict[str, Any]:
    """[SEARCH/RETRIEVE -> TRACE METRICS -> RERANK -> GENERATE RESPONSE]"""
    # 📝 OBSERVABILITY TRACE: Initialize request logging parameters
    req_id = generate_request_id()
    start_time = time.time()
    
    trace_metrics = {
        "request_id": req_id,
        "user": active_username,
        "user_query": query,
        "model_provider": settings.LLM_PROVIDER,
        "model_name": "gemini-3.6-flash" if settings.LLM_PROVIDER == "gemini" else "gpt-4o-mini",
        "raw_chunks_retrieved": 0,
        "reranked_chunks_selected": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "elapsed_seconds": 0.0,
        "estimated_cost_usd": 0.0,
        "errors_logged": []
    }
    
    print(f"🎬 [Request Received] ID: {req_id} | User: {active_username} initialized pipeline.")
    
    vector_store = get_azure_search_vector_store()
    tenant_filter_string = f"owner_username eq '{active_username}'"
    
    try:
        search_client = vector_store.client
        query_vector = vector_store.embedding_function.embed_query(query)
        
        from azure.search.documents.models import VectorizedQuery
        vector_query = VectorizedQuery(vector=query_vector, k_nearest_neighbors=top_k, fields="content_vector")
        
        # 🔍 EXECUTE RETRIEVAL SEARCH
        azure_results = search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            filter=tenant_filter_string,
            select=["id", "content", "metadata"],
            top=top_k
        )
        
        raw_retrieved_docs = []
        for result in azure_results:
            meta = result.get("metadata", {})
            doc_metadata = {
                "document_name": meta.get("document_name", "Unknown File"),
                "page_number": int(meta.get("page_number", 1)),
                "azure_blob_url": meta.get("azure_blob_url", ""),
                "owner_username": result.get("owner_username", active_username)
            }
            raw_retrieved_docs.append(Document(page_content=result.get("content", ""), metadata=doc_metadata))
            
        # 📝 OBSERVABILITY TRACE: Record raw retrieval metrics
        trace_metrics["raw_chunks_retrieved"] = len(raw_retrieved_docs)

        if len(raw_retrieved_docs) == 0:
            # Fallback bypass trace loop
            global_results = search_client.search(search_text=query, top=2)
            for r in global_results:
                raw_retrieved_docs.append(Document(page_content=r.get("content", ""), metadata={"document_name": "Bypass File", "page_number": 1, "azure_blob_url": ""}))

        # 🔀 EXECUTE RERANKING
        optimized_reranked_docs = simulate_cross_encoder_reranker(query, raw_retrieved_docs, top_n=2)
        trace_metrics["reranked_chunks_selected"] = len(optimized_reranked_docs)
        
        context_blocks = []
        for doc in optimized_reranked_docs:
            meta = doc.metadata
            context_blocks.append(f"[File: {meta.get('document_name')} | Page: {meta.get('page_number')}]: {doc.page_content}")
        formatted_context = "\n\n".join(context_blocks)

        # 🧠 INITIALIZE CONFIGURABLE MODEL GENERATION
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

        # 📝 OBSERVABILITY TRACE: Pre-calculate prompt token costs
        prompt_string_representation = f"{system_instruction} {formatted_context} {query}"
        in_tokens = estimate_token_count(prompt_string_representation)
        trace_metrics["input_tokens"] = in_tokens

        # Fire LLM request execution pass
        print(f"📡 [LLM Request] Forwarding payload prompt to {settings.LLM_PROVIDER} API...")
        structured_output = await rag_chain.ainvoke({"context": formatted_context, "question": query})
        print(f"✅ [LLM Response Status] 200 OK received smoothly.")

        # 📝 OBSERVABILITY TRACE: Post-calculate response token strings
        out_tokens = estimate_token_count(structured_output.synthesized_answer)
        trace_metrics["output_tokens"] = out_tokens
        trace_metrics["total_tokens"] = in_tokens + out_tokens
        
        # Finalize telemetry processing values
        trace_metrics["elapsed_seconds"] = time.time() - start_time
        trace_metrics["estimated_cost_usd"] = calculate_approximate_cost(in_tokens, out_tokens)
        
        # Print the trace report to the console terminal
        print_telemetry_trace_report(trace_metrics)

        isolated_sources_payload = []
        for doc in optimized_reranked_docs:
            isolated_sources_payload.append({
                "document_name": doc.metadata.get("document_name"),
                "page_number": doc.metadata.get("page_number"),
                "permanent_download_url": doc.metadata.get("azure_blob_url")
            })

        return {
            "observability_request_id": req_id, # Link request ID token payload to response schema card
            "ai_generated_answer": structured_output.synthesized_answer,
            "is_grounded_validation": structured_output.is_answer_fully_grounded,
            "search_precision_score": structured_output.confidence_score,
            "pages_cited_integers": structured_output.citations_page_list,
            "isolated_sources": isolated_sources_payload,
            "telemetry_metrics_summary": {
                "duration_seconds": round(trace_metrics["elapsed_seconds"], 3),
                "total_tokens_used": trace_metrics["total_tokens"],
                "transaction_cost_usd": f"${trace_metrics['estimated_cost_usd']:.7f}"
            }
        }
        
    except Exception as internal_crash_err:

        raw_error_log_string = str(internal_crash_err)
        clean_log = re.sub(r"AccountKey=[\w+/=]+", "AccountKey=[REDACTED]", raw_error_log_string)
        clean_log = re.sub(r"api-key=[\w]+", "api-key=[REDACTED]", clean_log)
        
        print(f"❌ [Internal Server Error Log] Cleansed Trace: {clean_log}")
    
        return {
            "ai_generated_answer": "An isolated enterprise communication exception occurred. The operation details have been logged securely for supervisor evaluation.",
            "is_grounded_validation": False,
            "search_precision_score": 0.0,
            "pages_cited_integers": [],
            "isolated_sources": []
        }
        
    except Exception as err:
        trace_metrics["errors_logged"].append(str(err))
        trace_metrics["elapsed_seconds"] = time.time() - start_time
        print_telemetry_trace_report(trace_metrics)
        return {"ai_generated_answer": f"Observability engine intercepted failure: {str(err)}", "isolated_sources": []}
