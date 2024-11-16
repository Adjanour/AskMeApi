import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.faq_router import router as faq_router
from sentence_transformers import SentenceTransformer
import spacy

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
    return {"message": "Hello World"}


@app.get("/chatbot/status")
async def chatbot_status():
    return {"status": "Chatbot is running"}


# Dependency Injection for Models
@asynccontextmanager
async def get_sentence_transformer():
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    yield model


@asynccontextmanager
async def get_spacy_nlp():
    nlp = spacy.load("en_core_web_sm")
    yield nlp


# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    logger.info("Application has started")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application is shutting down")


# Include FAQ Routes
app.include_router(faq_router, prefix="/api")
