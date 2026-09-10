from pydantic import BaseModel, Field, field_validator
import re

class UserSupportQueryInputSchema(BaseModel):
    """Strict Pydantic input sanitizer schema ensuring structured argument validity."""
    query: str = Field(..., min_length=3, max_length=500, description="Conversational query payload text")
    
    @field_validator("query")
    @classmethod
    def clean_and_validate_query_characters(cls, val: str) -> str:
        """Enforces clean semantic content values and sanitizes malicious script inputs."""
        stripped = val.strip()
        if not stripped:
            raise ValueError("Query string element cannot be blank or contain only space characters.")
            
        # Strip potential HTML script tags to prevent Cross-Site Scripting injections
        sanitized = re.sub(r"<script.*?>.*?</script.*?>", "", stripped, flags=re.IGNORECASE)
        return sanitized
