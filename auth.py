from fastapi import Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from db import get_tenant_by_api_key  # Assume this is a helper to retrieve tenant_id

api_key_header = APIKeyHeader(name="X-API-Key")


def get_api_key(api_key: str = Security(api_key_header)):
    tenant_id = get_tenant_by_api_key(api_key)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return tenant_id  # Optionally return tenant_id for further use
