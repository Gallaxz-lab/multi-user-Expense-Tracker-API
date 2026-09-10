import time
from fastapi import HTTPException
from app.schemas.expense import DBRateLimit
from app.database.connection import SessionLocal

def check_rate_limiting_guardrail(username: str, max_tokens: float = 2.0, refill_rate_per_sec: float = 0.1):
    if not username or username == "Unknown User":
        raise HTTPException(status_code=401, detail="Not Authenticated.")

    current_time = time.time()
    db = SessionLocal()
    
    try:
        user_record = db.query(DBRateLimit).filter(DBRateLimit.username == username).first()
        
        if not user_record:
            new_limit = DBRateLimit(
                username=username,
                last_check_time=current_time,
                current_tokens=max_tokens - 1.0
            )
            db.add(new_limit)
            db.commit()
            return

        elapsed_seconds = current_time - user_record.last_check_time
        refilled_tokens = user_record.current_tokens + (elapsed_seconds * refill_rate_per_sec)
        updated_tokens = min(max_tokens, refilled_tokens)
        
        if updated_tokens < 1.0:
            print(f"🚨 [RATE LIMIT BLOCKED] Wall tripped for: '{username}'")
            raise HTTPException(
                status_code=429, 
                detail="Too Many Requests: API speed cap exceeded."
            )
            
        user_record.last_check_time = current_time
        user_record.current_tokens = updated_tokens - 1.0
        db.add(user_record)
        db.commit()
        
    except HTTPException as handled_api_err:
        raise handled_api_err
    except Exception as e:
        db.rollback()
        print(f"❌ [Limiter Internal Error]: {str(e)}")
    finally:
        db.close()

def sanitize_prompt_injection_guardrail(user_input: str) -> str:
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
    max_bytes = max_mb * 1024 * 1024
    if len(content_bytes) > max_bytes:
        print(f"🛑 [Size Violation] Intercepted heavy payload size: {len(content_bytes)} bytes.")
        raise HTTPException(
            status_code=413,
            detail=f"Payload Too Large: Upload sizes are strictly capped at {max_mb}MB maximum."
        )
