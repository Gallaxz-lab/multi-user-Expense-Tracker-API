import time
import os
import json
from fastapi import HTTPException
from typing import Dict

# File-backed shared token bucket memory storage path to link multiple cloud worker processes
SHARED_LIMIT_FILE = "/tmp/render_shared_rate_limits.json"

def _load_shared_buckets() -> Dict[str, list]:
    """Reads the token bucket state from shared file memory."""
    if os.path.exists(SHARED_LIMIT_FILE):
        try:
            with open(SHARED_LIMIT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def _save_shared_buckets(data: Dict[str, list]):
    """Writes the updated token bucket state to shared file memory."""
    try:
        with open(SHARED_LIMIT_FILE, "w") as f:
            json.dump(data, f)
    except Exception:
        pass

def check_rate_limiting_guardrail(username: str, max_tokens: float = 2.0, refill_rate_per_sec: float = 0.1):
    """
    Implements a file-persistent token bucket limit across all cloud worker processes.
    Max 2 bursts, refills slowly (1 token every 10 seconds).
    """
    if not username or username == "Unknown User":
        raise HTTPException(
            status_code=401,
            detail="Not Authenticated: Safe block triggered due to missing user context token properties."
        )

    current_time = time.time()
    buckets = _load_shared_buckets()

    if username not in buckets:
        # Initialize user bucket state array format [last_check_time, current_tokens]
        buckets[username] = [current_time, max_tokens]
        _save_shared_buckets(buckets)
        return

    last_check, tokens = buckets[username]
    
    # Calculate token accumulation delta values over time intervals
    elapsed = current_time - last_check
    refilled_tokens = tokens + (elapsed * refill_rate_per_sec)
    tokens = min(max_tokens, refilled_tokens)
    
    if tokens < 1.0:
        print(f"⚠️ [Security Alarm] Shared Rate limit tripped for user: '{username}'!")
        raise HTTPException(
            status_code=429, 
            detail="Too Many Requests: API speed cap exceeded. Please pace your communication loops."
        )
        
    # Spend 1 token, update state arrays, and commit back to the persistent file partition
    buckets[username] = [current_time, tokens - 1.0]
    _save_shared_buckets(buckets)


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
