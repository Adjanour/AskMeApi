import json
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.security import APIKeyHeader
import csv
import logging

from starlette.responses import StreamingResponse

from app.embeddings import EmbeddingsHandler, LLMHandler
from app.models import TenantRequest, QueryRequest
from app.sqlite_db import SQLiteDB
from app.mongodb_db import MongoDBAsync as MongoDB
from app.db_interface import DBInterface
from app.utils import stream_words

router = APIRouter()

# Logging setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Configuration
db_backend = "mongodb"  # Use "sqlite" or "mongodb"


# Database instance singleton
def get_db() -> DBInterface:
    if db_backend == "sqlite":
        return SQLiteDB()
    elif db_backend == "mongodb":
        return MongoDB()


api_key_header = APIKeyHeader(name="X-API-Key")


# Function to get the tenant by API key
async def get_tenant_by_api_key(api_key: str, db: DBInterface) -> Optional[str]:
    return await db.get_tenant_by_api_key(api_key)


# Dependency to inject EmbeddingsHandler
async def get_embeddings_handler(db: DBInterface = Depends(get_db)) -> EmbeddingsHandler:
    return EmbeddingsHandler(db=db)


# Dependency: Get and validate API key
async def get_api_key(api_key: str = Depends(api_key_header), db: DBInterface = Depends(get_db)):
    tenant_id = await get_tenant_by_api_key(api_key, db)
    if tenant_id is None:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return tenant_id


# Utility: Stream the lines from a CSV file asynchronously
async def stream_csv_lines(file: UploadFile) -> AsyncGenerator[dict, None]:
    file_content = (await file.read()).decode("utf-8")
    reader = csv.DictReader(file_content.splitlines())
    for row in reader:
        yield row


# Upload FAQ endpoint
@router.post("/upload-faq")
async def upload_faq(
        file: UploadFile = File(...),
        tenant_id: str = Depends(get_api_key),
        db: DBInterface = Depends(get_db)
):
    try:
        # Ensure tenant_id is valid
        if tenant_id is None:
            raise HTTPException(status_code=401, detail="Invalid API key")

        # Validate file format and load data
        if file.filename.endswith(".json"):
            faq_data = json.load(file.file)
        elif file.filename.endswith(".csv"):
            faq_data = [row async for row in stream_csv_lines(file)]
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format")

        # Validate data structure
        required_fields = {"question", "answer"}
        for faq in faq_data:
            if not required_fields.issubset(faq):
                raise HTTPException(status_code=400, detail="Missing required fields in the data")

        print("processing faq data", faq_data)
        # Process and store embeddings
        embeddings_handler = EmbeddingsHandler(db=db)
        await embeddings_handler.store_faq_embeddings(faq_data, tenant_id)

        return {"message": "FAQ data uploaded and processed successfully"}

    except Exception as e:
        logger.error("Error during FAQ upload", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ask")
async def query_faq(
        query: QueryRequest,
        embeddings_handler: EmbeddingsHandler = Depends(get_embeddings_handler),
        tenant_id: str = Depends(get_api_key)
):
    try:
        # Find similar FAQs using embeddings
        similar_faqs = await embeddings_handler.find_similar_faqs(query.question, tenant_id)

        if not similar_faqs:
            raise HTTPException(status_code=404, detail="No similar FAQs found")

        # Stream response
        return StreamingResponse(
            content=stream_words(similar_faqs[0]["answer"], 0.1),
            media_type="text/event-stream"
        )

    except Exception as e:
        logger.error("Error during FAQ query", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to process query")


# Create tenant endpoint
@router.post("/create-tenant")
async def create_tenant_endpoint(
        tenant_request: TenantRequest,
        db: DBInterface = Depends(get_db)
):
    try:
        logger.info(f"Creating tenant: {tenant_request.name}")
        tenant_info = await db.create_tenant(tenant_request.name, tenant_request.config_settings)
        return {
            "message": "Tenant created successfully",
            "tenant_info": tenant_info
        }
    except ValueError as ve:
        logger.error("Validation error during tenant creation", exc_info=True)
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error("Error during tenant creation", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create tenant")
