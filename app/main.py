import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.faq_router import router as faq_router

from app.models import ModelSingleton

# Setup logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize models asynchronously
    try:
        await ModelSingleton.initialize()
        yield
    except Exception as e:
        logger.error(f"Failed to initialize models: {str(e)}")
        raise

# Initialize FastAPI app
app = FastAPI(lifespan=lifespan)



# CORS Configuration
allowed_domains = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_domains,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck Endpoints
@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/chatbot/status")
async def chatbot_status():
    return {"status": "Chatbot is running"}


# Include FAQ Routes
app.include_router(faq_router, prefix="/api")