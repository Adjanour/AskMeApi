from pydantic import BaseModel
from typing import Optional, Dict, List


class TenantRequest(BaseModel):
    name: str
    config_settings: Optional[Dict[str, str]] = None


class QueryRequest(BaseModel):
    question: str
    conversation_history: List[Dict[str, str]] = None  # A list of messages
