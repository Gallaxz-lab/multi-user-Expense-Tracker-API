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
    query: str = Field(..., min_length=3, max_length=500)
    
    @field_validator("query")
    @classmethod
    def clean_and_validate_query_characters(cls, val: str) -> str:
        if not val or not val.strip():
            raise HTTPException(
                status_code=422,
                detail="Unprocessable Entity: Query string field content value cannot be blank or contain only space characters."
            )
        stripped = val.strip()
        sanitized = re.sub(r"<script.*?>.*?</script.*?>", "", stripped, flags=re.IGNORECASE)
        return sanitized
