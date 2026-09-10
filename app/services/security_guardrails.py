import time
import os
import json
from fastapi import HTTPException
from typing import Dict
import time
from fastapi import HTTPException
from app.database.connection import get_db, SessionLocal
from app.schemas.expense import DBRateLimit

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
    Persistent Database Token Bucket Limiter.
    Forces all Render web servers to read from your live shared PostgreSQL tables.
    """
    if not username or username == "Unknown User":
        raise HTTPException(
            status_code=401,
            detail="Not Authenticated: Missing active user profile parameters."
        )

    current_time = time.time()

    db = SessionLocal()
    try:
        # 🔍 Look up your rate limiting row properties
        user_record = db.query(DBRateLimit).filter(DBRateLimit.username == username).first()
        
        if not user_record:
            # First request: save initial bucket token arrays straight to database
            new_limit = DBRateLimit(
                username=username,
                last_check_time=current_time,
                current_tokens=max_tokens - 1.0 # Spend first token instantly
            )
            db.add(new_limit)
            db.commit()
            return


        elapsed_seconds = current_time - user_record.last_check_time
        refilled_tokens = user_record.current_tokens + (elapsed_seconds * refill_rate_per_sec)
        updated_tokens = min(max_tokens, refilled_tokens)
        

        if updated_tokens < 1.0:
            print(f"🚨 [POSTGRESQL RATE LIMIT ALARM] Persistent speed wall tripped for user: '{username}'!")
            raise HTTPException(
                status_code=429, 
                detail="Too Many Requests: API speed cap exceeded. Please pace your communication loops."
            )
            

        user_record.last_check_time = current_time
        user_record.current_tokens = updated_tokens - 1.0
        
        db.add(user_record)
        db.commit() 
        db.refresh(user_record) 
        
        print(f"🔒 Security Guardrail: Spent 1 token for user '{username}'. Tokens remaining: {updated_tokens - 1.0:.2f}")

    except HTTPException as handled_api_err:
        db.rollback()  # Rollback transactional items if rate limit trips
        raise handled_api_err
    except Exception as e:
        db.rollback()  # Rollback row mutations if an internal exception occurs
        print(f"❌ [Limiter Exception]: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal tracking limiter exception.")
    finally:
        db.close() 

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
