import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer
from app.faq_router import router as faq_router
import spacy
import asyncio
from functools import lru_cache, wraps

from app.models import ModelSingleton


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize models asynchronously
    """
    Manage the lifecycle of the application's models using an asynchronous context manager.
    
    This context manager handles the initialization and uninitialization of the application's singleton model
    during the FastAPI application startup and shutdown phases.
    
    Yields control back to the application after initializing models, allowing the application to run.
    When the application is shutting down, it ensures proper cleanup of model resources.
    
    Yields:
        None: Provides a hook for the FastAPI application lifecycle management
    
    Side Effects:
        - Initializes ModelSingleton when the application starts
        - Uninitializes ModelSingleton when the application shuts down
    """
    await ModelSingleton.initialize()
    yield
    await ModelSingleton.uninitialize()

# Initialize FastAPI app
app = FastAPI()

# Setup logging
logger = logging.getLogger("uvicorn")
logger.setLevel(logging.INFO)

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
    """
    Return a simple greeting message for the root endpoint.
    
    Returns:
        dict: A dictionary containing a welcome message
    """
    return {"message": "Hello World"}

@app.get("/chatbot/status")
async def chatbot_status():
    """
    Return the current status of the chatbot.
    
    Returns:
        dict: A dictionary containing the current status of the chatbot, with a single key 'status' indicating that the chatbot is operational.
    """
    return {"status": "Chatbot is running"}


@app.on_event("startup")
async def startup_event():
    # Initialize models asynchronously
    """
    Asynchronously initialize the singleton model during application startup.
    
    This event handler is triggered when the FastAPI application starts, ensuring that the 
    ModelSingleton is properly initialized and ready to serve requests. It calls the 
    class method `initialize()` to set up necessary models and resources.
    
    Note:
        This method is typically used with FastAPI's startup event mechanism to prepare 
        application resources before handling incoming requests.
    """
    await ModelSingleton.initialize()

# Include FAQ Routes
app.include_router(faq_router, prefix="/api")
