# app/config.py
import os

class Config:
    API_KEY = os.getenv("API_KEY", "default_api_key")
    EMBEDDING_MODEL_NAME = "distilbert-base-uncased"
    MAX_FAQ_RESULTS = 5
    # More configurations as needed
