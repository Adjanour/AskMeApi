from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.faq_router import router as faq_router
from sentence_transformers import SentenceTransformer
import spacy


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    # Load Sentence Transformers
    sentence_model_name = "all-MiniLM-L6-v2"
    sentence_transformer = SentenceTransformer(sentence_model_name)

    # Load SpaCy
    nlp = spacy.load("en_core_web_md")
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/chatbot/status")
async def chatbot_status():
    return {"status": "Chatbot is running"}


# Include routes
app.include_router(faq_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
