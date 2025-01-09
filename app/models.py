import asyncio

import spacy
from pydantic import BaseModel
from typing import Optional, Dict, List

from sentence_transformers import SentenceTransformer


class TenantRequest(BaseModel):
    name: str
    config_settings: Optional[Dict[str, str]] = None


class QueryRequest(BaseModel):
    question: str


class ModelSingleton:
    _sentence_transformer = None
    _spacy_nlp = None

    @classmethod
    async def initialize(cls):
        """
        Asynchronously initialize SentenceTransformer and spaCy NLP models.
        
        This method pre-loads machine learning models during application startup to ensure they are ready for use. It uses asyncio's to_thread to load models in a non-blocking manner, preventing performance bottlenecks during initialization.
        
        Parameters:
            cls (type): The class itself (ModelSingleton) used for storing model instances.
        
        Notes:
            - Loads 'all-MiniLM-L6-v2' SentenceTransformer model
            - Loads 'en_core_web_sm' spaCy language model
            - Models are loaded only once to optimize resource usage
            - Subsequent calls will not reload already initialized models
        
        Raises:
            Exception: If model loading fails due to network or resource issues
        """
        if cls._sentence_transformer is None:
            cls._sentence_transformer = await asyncio.to_thread(SentenceTransformer, 'all-MiniLM-L6-v2')
        if cls._spacy_nlp is None:
            cls._spacy_nlp = await asyncio.to_thread(spacy.load, 'en_core_web_sm')

    @classmethod
    async def uninitialize(cls):
        """
        Asynchronously unload and reset the SentenceTransformer and spaCy NLP models.
        
        This method sets both the sentence transformer and spaCy NLP model instances to None,
        effectively releasing their resources and preparing them for reinitialization.
        
        Note:
            - Does not raise any exceptions if models are already None
            - Safely handles model deallocation
            - Part of the ModelSingleton's resource management strategy
        """
        if cls._sentence_transformer is not None:
            cls._sentence_transformer = None
        if cls._spacy_nlp is not None:
            cls._spacy_nlp = None

    @classmethod
    def get_sentence_transformer(cls):
        """
        Get the current SentenceTransformer model instance.
        
        Returns:
            SentenceTransformer: The initialized SentenceTransformer model, or None if not yet loaded.
        """
        return cls._sentence_transformer

    @classmethod
    def get_spacy_nlp(cls):
        """
        Get the spaCy NLP model instance.
        
        Returns:
            spacy.language.Language: The initialized spaCy NLP model, or None if not loaded.
        """
        return cls._spacy_nlp
