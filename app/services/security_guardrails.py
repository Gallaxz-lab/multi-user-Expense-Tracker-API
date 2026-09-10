import time
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Tuple

security_bearer = HTTPBearer()


user_rate_limit_buckets: Dict[str, Tuple[float, float]] = {} # {username: (last_check_time, current_tokens)}

def check_rate_limiting_guardrail(username: str, max_tokens: float = 2.0, refill_rate_per_sec: float = 0.1):
    if not username or username == "Unknown User":
        raise HTTPException(
            status_code=401,
            detail="Not Authenticated: Safe block triggered due to missing user context token properties."
        )
    current_time = time.time()
    if username not in user_rate_limit_buckets:
        user_rate_limit_buckets[username] = (current_time, max_tokens)
        return
    last_check, tokens = user_rate_limit_buckets[username]
    elapsed = current_time - last_check
    refilled_tokens = tokens + (elapsed * refill_rate_per_sec)
    tokens = min(max_tokens, refilled_tokens)
    if tokens < 1.0:
        print(f"⚠️ [Security Alarm] Rate limit tripped for user: '{username}'!")
        raise HTTPException(
            status_code=429, 
            detail="Too Many Requests: API speed cap exceeded. Please pace your communication loops."
        )
    user_rate_limit_buckets[username] = (current_time, tokens - 1.0)

def sanitize_prompt_injection_guardrail(user_input: str) -> str:
    """Blocks adversarial payload patterns attempting to manipulate system instructions."""
    if not user_input:
        return user_input
        
    input_lower = user_input.lower()
    
    malicious_signatures = [
        "ignore previous instructions", 
        "system prompt override", 
        "you are now an unfiltered", 
        "forget your rules",
        "output raw password keys",
        "act as a malicious terminal"
    ]
    
    if any(sig in input_lower for sig in malicious_signatures):
        print(f"🛑 [Jailbreak Blocked] Prompt injection signature intercepted in user text payload!")
        raise HTTPException(
            status_code=400,
            detail="Security Violation Mismatch: Dangerous system control override command signatures detected."
        )
        
    return user_input


def validate_payload_size_limits(content_bytes: bytes, max_mb: int = 5):
    """Guards server RAM channels from memory exhaustion denial-of-service attacks."""
    max_bytes = max_mb * 1024 * 1024
    if len(content_bytes) > max_bytes:
        print(f"🛑 [Size Violation] Intercepted heavy payload size: {len(content_bytes)} bytes.")
        raise HTTPException(
            status_code=413,
            detail=f"Payload Too Large: Upload sizes are strictly capped at {max_mb}MB maximum."
        )
