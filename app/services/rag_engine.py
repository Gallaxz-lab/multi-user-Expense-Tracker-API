from pydantic import BaseModel, Field
from typing import List, Dict, Any
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from app.config import settings
from app.services.vector_store import get_azure_search_vector_store

# Structured response schema for enterprise operational safety validation checks
class EnterpriseGroundedResponse(BaseModel):
    is_answer_fully_grounded: bool = Field(description="True if supported by context. False if missing information.")
    confidence_score: float = Field(description="Accuracy weight from 0.0 to 1.0 based on context matching.")
    synthesized_answer: str = Field(description="The formal answer built strictly from the text blocks.")
    citations_page_list: List[int] = Field(description="Array of document page numbers explicitly used.")

# Initialize the Gemini model for generation tasks
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=settings.GEMINI_API_KEY,
    temperature=0.1
)

# Enforce our structured output constraints using the native LangChain parser
structured_parser = PydanticOutputParser(pydantic_object=EnterpriseGroundedResponse)

def format_context_documents(docs: List[Any]) -> str:
    context_blocks = []
    for doc in docs:
        meta = doc.metadata
        context_blocks.append(f"[Source Page: {meta.get('page_number')} | Permanent Cloud URL: {meta.get('azure_blob_url')}]: {doc.page_content}")
    return "\n\n".join(context_blocks)

async def run_langchain_rag_pipeline(query: str, top_k: int = 3) -> Dict[str, Any]:
    """[AZURE SEARCH + GEMINI GENERATION MULTI-PROVIDER ENGINE]"""
    vector_store = get_azure_search_vector_store()
    
    # NATIVE AZURE HYBRID RETRIEVAL (Combines Cloud Vectors and Text Tokens in one step)
    azure_hybrid_retriever = vector_store.as_retriever(
        search_type="hybrid",
        search_kwargs={"k": top_k}
    )
    
    try:
        retrieved_documents = azure_hybrid_retriever.invoke(query)
        formatted_context = format_context_documents(retrieved_documents)

        system_instruction = (
            "You are an enterprise compliance assistant. Answer the user question using ONLY the provided context blocks.\n"
            "You must format your output according to these strict parsing instructions:\n{format_instructions}\n\n"
            "Context:\n{context}"
        )
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instruction),
            ("human", "{question}")
        ])

        final_prompt = prompt.partial(format_instructions=structured_parser.get_format_instructions())
        rag_chain = final_prompt | llm | structured_parser

        # Run the generation pass
        structured_output = await rag_chain.ainvoke({"context": formatted_context, "question": query})

        sources_metadata = []
        for doc in retrieved_documents:
            sources_metadata.append({
                "document_name": doc.metadata.get("document_name"),
                "page_number": doc.metadata.get("page_number"),
                "azure_permanent_blob_url": doc.metadata.get("azure_blob_url")
            })

        return {
            "answer": structured_output.synthesized_answer,
            "is_grounded": structured_output.is_answer_fully_grounded,
            "confidence_metrics_weight": structured_output.confidence_score,
            "pages_cited_by_ai": structured_output.citations_page_list,
            "sources": sources_metadata
        }

    except Exception as err:
        print(f"❌ Enterprise Multi-Provider Pipeline Error: {str(err)}")
        return {
            "answer": f"A RAG execution pipeline connectivity error occurred: {str(err)}",
            "sources": []
        }
