import asyncio

import spacy
from pydantic import BaseModel
from typing import Optional, Dict

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
        Pre-load models asynchronously on startup.
        This should only be called once during the application startup.
        """
        if cls._sentence_transformer is None:
            cls._sentence_transformer = await asyncio.to_thread(SentenceTransformer, 'all-MiniLM-L6-v2')
        if cls._spacy_nlp is None:
            cls._spacy_nlp = await asyncio.to_thread(spacy.load, 'en_core_web_sm')

    @classmethod
    async def uninitialize(cls):
        if cls._sentence_transformer is not None:
            cls._sentence_transformer = None
        if cls._spacy_nlp is not None:
            cls._spacy_nlp = None

    @classmethod
    def get_sentence_transformer(cls):
        return cls._sentence_transformer

    @classmethod
    def get_spacy_nlp(cls):
        return cls._spacy_nlp
