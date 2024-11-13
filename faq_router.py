# app/faq_router.py
import json
import sqlite3
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
import csv
from embeddings import EmbeddingsHandler, LLMHandler
from models import TenantRequest
from sqlite_db import SQLiteDB
from mongodb_db import MongoDB
from db_interface import DBInterface

router = APIRouter()

# Choose the database backend (SQLite or MongoDB)
db_backend = "sqlite"  # Change to "mongodb" to switch to MongoDB


def get_db() -> DBInterface:
    if db_backend == "sqlite":
        return SQLiteDB()
    elif db_backend == "mongodb":
        return MongoDB()


api_key_header = APIKeyHeader(name="X-API-Key")


# Function to get the tenant by API key
def get_tenant_by_api_key(api_key: str, db: DBInterface) -> Optional[int]:
    print("db")
    print(db)  # This will print the actual DB instance
    return db.get_tenant_by_api_key(api_key)


# Function to get API key and validate
def get_api_key(api_key: str = Depends(api_key_header), db: DBInterface = Depends(get_db)):
    print("db1")
    print(db)  # This will print the actual DB instance
    tenant_id = get_tenant_by_api_key(api_key, db)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return tenant_id  # Return the tenant ID


# FastAPI route for uploading FAQ data
@router.post("/upload-faq")
async def upload_faq(file: UploadFile = File(...), tenant_id: int = Depends(get_api_key),db: DBInterface = Depends(get_db)):
    try:
        # Here, the tenant_id is already validated by get_api_key
        if tenant_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")

        if file.filename.endswith(".json"):
            faq_data = json.load(file.file)
        elif file.filename.endswith(".csv"):
            faq_data = []
            reader = csv.DictReader(file.file)
            for row in reader:
                faq_data.append(row)
        else:
            raise HTTPException(status_code=400, detail="File format not supported")

        # Processing embeddings
        embeddings_handler = EmbeddingsHandler(db=db)
        embeddings_handler.store_faq_embeddings(faq_data, tenant_id)

        return {"message": "FAQ data uploaded and processed successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-faq")
async def query_faq(query: str, api_key: str):
    tenant_id = get_tenant_by_api_key(api_key)
    if tenant_id is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    embedding_handler = EmbeddingsHandler()
    llm_handler = LLMHandler()
    similar_faqs = embedding_handler.find_similar_faqs(query)

    if not similar_faqs:
        raise HTTPException(status_code=404, detail="No similar FAQs found")

    prompt = llm_handler.generate_llama_prompt(similar_faqs, query)
    llm_handler.stream_llama_response(prompt)


@router.post("/create-tenant")
async def create_tenant_endpoint(tenant_request: TenantRequest, db: DBInterface = Depends(get_db)):
    try:
        name = tenant_request.name
        config_settings = tenant_request.config_settings
        print(f"Creating tenant: {name}")
        tenant_info = db.create_tenant(name, config_settings)
        return {
            "message": "Tenant created successfully",
            "tenant_info": tenant_info  # Return API key and other details
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create tenant")
