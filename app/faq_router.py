# app/faq_router.py
from fastapi import APIRouter, Depends, HTTPException
from pinecone import Pinecone

from starlette.responses import StreamingResponse

from app.embeddings import EmbeddingsHandler
from app.models import QueryRequest, ModelSingleton
from app.utils import stream_words

router = APIRouter()


# Dependency injection for EmbeddingsHandler
async def get_embeddings_handler() -> EmbeddingsHandler:
    """
    Asynchronously create and return an EmbeddingsHandler for FAQ processing.
    
    This function initializes an EmbeddingsHandler by retrieving necessary models and creating a Pinecone index connection. It uses ModelSingleton to obtain a sentence transformer and spaCy NLP model, and establishes a connection to a Pinecone index named "askme".
    
    Returns:
        EmbeddingsHandler: A configured handler for generating and searching FAQ embeddings, ready for use in query processing.
    """
    sentence_transformer = ModelSingleton.get_sentence_transformer()
    spacy_nlp = ModelSingleton.get_spacy_nlp()
    pinecone_index = Pinecone(api_key="pcsk_5k4s6Z_4mMX815ACLEuHfTAKmiDk775uXiUd6NCvNrodqnfbcC3CRQtMTgcqaWGrmpnWTi").Index("askme")
    return EmbeddingsHandler(spacy_nlp, sentence_transformer, pinecone_index)



@router.post("/ask")
async def query_faq(query: QueryRequest,embeddings_handler: EmbeddingsHandler = Depends(get_embeddings_handler)):
    """
    Process a user's FAQ query by finding and returning the most similar FAQ answer.
    
    Handles retrieving relevant FAQ answers using semantic similarity search with embeddings. 
    If no similar FAQs are found, raises a 404 HTTP exception.
    
    Parameters:
        query (QueryRequest): The user's query containing the question to search
        embeddings_handler (EmbeddingsHandler, optional): Handler for processing FAQ embeddings. 
            Defaults to dependency-injected instance from get_embeddings_handler().
    
    Returns:
        dict: A dictionary containing the most relevant FAQ answer
    
    Raises:
        HTTPException: 404 error if no similar FAQs are found for the given query
    """
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
