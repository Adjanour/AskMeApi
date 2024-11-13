from pydantic import BaseModel
from typing import Optional, Dict


class TenantRequest(BaseModel):
    name: str
    config_settings: Optional[Dict[str, str]] = None
