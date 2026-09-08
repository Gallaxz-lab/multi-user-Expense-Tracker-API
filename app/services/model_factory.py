from langchain_core.language_models.chat_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.config import settings

def get_configurable_llm_provider() -> BaseChatModel:
    """[MAKE YOUR LLM PROVIDER CONFIGURABLE THROUGH ENVIRONMENT VARIABLES]"""
    provider = settings.LLM_PROVIDER.lower().strip()
    
    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            raise ValueError("Configuration Error: GEMINI_API_KEY variable is missing.")
        return ChatGoogleGenerativeAI(
            model="gemini-3.6-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            model_kwargs={"response_mime_type": "application/json"}
        )
        
    elif provider == "openai":
        if not settings.OPENAI_API_KEY:
            raise ValueError("Configuration Error: OPENAI_API_KEY variable is missing.")
        return ChatOpenAI(
            model="gpt-4o-mini",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        
    elif provider == "anthropic":
        if not settings.ANTHROPIC_API_KEY:
            raise ValueError("Configuration Error: ANTHROPIC_API_KEY variable is missing.")
        return ChatAnthropic(
            model="claude-3-5-haiku-latest",
            api_key=settings.ANTHROPIC_API_KEY,
            temperature=0.1
        )
        
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER allocation token string: '{provider}'")
