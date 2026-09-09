import time
import uuid
import re
from typing import Dict, Any, List
from app.config import settings

def generate_request_id() -> str:
    """Generates a unique tracking token ID identifier string for a request pipeline."""
    return f"req-{uuid.uuid4().hex[:8]}"

def estimate_token_count(text: str) -> int:
    """
    Heuristic rule: 1 token is approximately 4 characters of text.
    Provides a safe, local fallback estimation metric to prevent API overhead.
    """
    if not text:
        return 0
    return max(1, int(len(text) / 4))

def calculate_approximate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculates enterprise model routing expenditure statistics in USD."""
    provider = settings.LLM_PROVIDER.lower().strip()
    
    # ─── COST SPECIFICATION RULES ───
    if provider == "gemini":
        input_rate = 0.075 / 1_000_000
        output_rate = 0.30 / 1_000_000
    elif provider == "openai":
        input_rate = 0.15 / 1_000_000
        output_rate = 0.60 / 1_000_000
    elif provider == "anthropic":
        input_rate = 0.25 / 1_000_000
        output_rate = 1.25 / 1_000_000
    else:
        input_rate = 0.0
        output_rate = 0.0
        
    return (input_tokens * input_rate) + (output_tokens * output_rate)


def print_telemetry_trace_report(metrics: Dict[str, Any]):
    """Prints a clear, structured telemetry report to the server terminal."""
    print("\n" + "═"*60)
    print(f"📡 [ENTERPRISE OBSERVABILITY TRACE REPORT] - ID: {metrics.get('request_id')}")
    print("═"*60)
    print(f"👤 User Context   : {metrics.get('user')}")
    print(f"🧠 Active Model   : {metrics.get('model_provider')} ({metrics.get('model_name')})")
    print(f"💬 User Question  : \"{metrics.get('user_query')}\"")
    print("─"*60)
    print(f"🔍 Cloud Search   : {metrics.get('raw_chunks_retrieved')} chunks fetched from Azure AI Search")
    print(f"📶 Cross-Reranker : Sorted & pruned down to {metrics.get('reranked_chunks_selected')} chunks")
    print("─"*60)
    print(f"⏱️ Response Time  : {metrics.get('elapsed_seconds'):.3f} seconds")
    print(f"🎟️ Token Usage    : In: {metrics.get('input_tokens')} | Out: {metrics.get('output_tokens')} | Total: {metrics.get('total_tokens')}")
    print(f"💵 Transaction Cost: ${metrics.get('estimated_cost_usd'):.8f} USD")
    
    if metrics.get("errors_logged"):
        print("─"*60)
        print(f"❌ Caught Exceptions: {metrics.get('errors_logged')}")
        
    print("═"*60 + "\n")