# app/faq_router.py
import os

from fastapi import APIRouter, Depends, HTTPException
from pinecone import Pinecone

from starlette.responses import StreamingResponse

from app.embeddings import EmbeddingsHandler
from app.models import QueryRequest, ModelSingleton
from app.utils import stream_words

router = APIRouter()


# Dependency injection for EmbeddingsHandler
async def get_embeddings_handler() -> EmbeddingsHandler:
    sentence_transformer = ModelSingleton.get_sentence_transformer()
    spacy_nlp = ModelSingleton.get_spacy_nlp()
    pinecone_index = Pinecone(api_key=os.environ.get("PINECONE_API_KEY")).Index("askme")
    return EmbeddingsHandler(spacy_nlp, sentence_transformer, pinecone_index)



@router.post("/ask")
async def query_faq(query: QueryRequest,embeddings_handler: EmbeddingsHandler = Depends(get_embeddings_handler)):
    print(query)

    similar_faqs = await embeddings_handler.find_similar_faqs(query.question,"6737dbd77a064a2893c302ad" )

    print(similar_faqs)
   
    if not similar_faqs:
        raise HTTPException(status_code=404, detail="No similar FAQs found")

    # prompt = llm_handler.generate_llama_prompt(similar_faqs, query.question, query.conversation_history)

    # return StreamingResponse(
    #     content=stream_words(similar_faqs[0]["answer"], 0.2),
    #     media_type="text/event-stream"
    # )
    return {"results": similar_faqs[0]["answer"]}
