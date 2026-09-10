from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import re 
from fastapi import FastAPI, HTTPException

class SupportRouterState(TypedDict):
    user_query: str
    current_user: Dict[str, Any]
    next_step: Optional[str]
    executed_tools: List[str]
    tool_results: Dict[str, Any]
    tool_error_logs: List[str]
    loop_count: int
    security_clearance_blocked: bool
    human_escalation_required: bool
    final_response: Optional[str]


class UserSupportQueryInputSchema(BaseModel):
    """Strict Pydantic input sanitizer ensuring request validity at the API gateway."""
    query: str = Field(..., min_length=3, max_length=500, description="Conversational query payload text")

    @field_validator("query")
    @classmethod
    def clean_and_validate_query_characters(cls, val: str) -> str:
        """Enforces clean semantic content values and prevents empty space strings."""
        if not val or not val.strip(): 
            raise HTTPException(
                status_code=422,
                detail="Unprocessable Entity: Query string field content value cannot be blank or contain only space characters."
            )
            
        stripped = val.strip()
        # Strip potential HTML script tags to prevent Cross-Site Scripting (XSS) injections
        sanitized = re.sub(r"<script.*?>.*?</script.*?>", "", stripped, flags=re.IGNORECASE)
        return sanitized
