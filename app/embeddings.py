import json
import pickle
import numpy as np
import faiss
import spacy
from functools import lru_cache

from ollama import AsyncClient
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
from app.db_interface import DBInterface

# Load models globally (to avoid redundant initializations)
nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])  # Disable unused components
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


# EmbeddingsHandler for FAQ management and similarity search
class EmbeddingsHandler:
    def __init__(self, db: DBInterface, embedding_dim: int = 384):
        self.db = db
        self.embedding_dim = embedding_dim
        self.indexes = {}  # Tenant-specific FAISS indexes

    @staticmethod
    def preprocess_text(text: str) -> str:
        """Lemmatize text and remove stop words."""
        doc = nlp(text.lower())
        tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
        return " ".join(tokens)

    @staticmethod
    def preprocess_texts(texts: List[str]) -> List[str]:
        """Batch preprocess texts."""
        docs = nlp.pipe(text.lower() for text in texts)
        return [" ".join(token.lemma_ for token in doc if not token.is_stop and token.is_alpha) for doc in docs]

    @staticmethod
    def embed_texts(texts: List[str]) -> np.ndarray:
        """Batch embed multiple texts."""
        return embedding_model.encode(texts)

    async def store_faq_embeddings(self, faqs: List[Dict[str, str]], tenant_id: str):
        """Embed and store FAQs in the database."""
        processed_questions = self.preprocess_texts([faq["question"] for faq in faqs])
        print("processed_questions", processed_questions)
        embeddings = self.embed_texts(processed_questions)
        print("embeddings", embeddings)

        await self.db.add_faq_bulk(tenant_id, faqs, embeddings)
        #
        # for faq, embedding in zip(faqs, embeddings):
        #     print("faq", faq)
        #     print("embedding", embedding)
        #     await self.db.add_faq(
        #         tenant_id,
        #         faq["question"],
        #         faq["answer"],
        #         pickle.dumps(embedding)
        #     )

        return None

    async def load_faq_embeddings(self, tenant_id: str):
        """Load embeddings for a given tenant ID."""
        faqs = await self.db.get_faqs(tenant_id)
        embeddings = np.array([pickle.loads(faq["embedding"]) for faq in faqs])
        return faqs, embeddings

    @lru_cache(128)
    async def find_similar_faqs(self, query: str, tenant_id: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find top similar FAQs for the given query."""
        processed_query = self.preprocess_text(query)
        query_embedding = self.embed_texts([processed_query]).reshape(1, -1)

        # Load or create tenant-specific FAISS index
        if tenant_id not in self.indexes:
            self.indexes[tenant_id] = faiss.IndexFlatL2(self.embedding_dim)
            faqs, embeddings = await self.load_faq_embeddings(tenant_id)
            self.indexes[tenant_id].add(embeddings)

        index = self.indexes[tenant_id]

        # Perform similarity search
        distances, indices = index.search(query_embedding, top_k)
        faqs, _ = await self.load_faq_embeddings(tenant_id)

        return [
            {
                "question": faqs[i]["question"],
                "answer": faqs[i]["answer"],
                "distance": distances[0][j]
            }
            for j, i in enumerate(indices[0])
        ]


# LLMHandler for interacting with the LLM
class LLMHandler:
    @staticmethod
    def generate_llama_prompt(
            similar_faqs: List[Dict[str, Any]],
            user_query: str,
            conversation_history: List[Dict[str, str]] = []
    ) -> str:
        """Generate a focused prompt for the LLM."""
        faq_context = "\n\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in similar_faqs])
        conversation_context = "\n".join(
            [f"{msg['role'].capitalize()}: {msg['content']}" for msg in conversation_history]
        )

        prompt = (
            f"You are a customer support chatbot designed to give precise answers based on the provided FAQ.\n\n"
            f"FAQs:\n{faq_context}\n\n"
            f"Conversation so far:\n{conversation_context}\n\n"
            f"User question: {user_query}\n\n"
            f"Please provide a clear and concise answer based on the information above."
        )

        return prompt

    @staticmethod
    async def stream_llama_response(prompt: str, model: str = "llama3.2:1b") -> str:
        """Stream the LLM response."""
        try:
            async for part in await AsyncClient().chat(
                    model=model,
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True
            ):
                yield f"data: {json.dumps(part['message']['content'])}\n\n"
        except Exception as e:
            yield f"data: Error occurred while streaming: {e}\n\n"
