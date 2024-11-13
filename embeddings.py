import json
import pickle
import numpy as np
import requests
import faiss
import spacy
import sqlite3
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple, Any

from db_interface import DBInterface

# Initialize spaCy English model for NLP
nlp = spacy.load("en_core_web_sm")

# Initialize Sentence Transformer model for embeddings
embedding_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')


# Initialize FAISS index
class EmbeddingsHandler:

    def __init__(self, db: DBInterface, embedding_dim: int = 384):
        self.db = db
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatL2(self.embedding_dim)  # For in-memory search

    @staticmethod
    def preprocess_text(text: str) -> str:
        """Lemmatize text and remove stop words."""
        doc = nlp(text.lower())
        tokens = [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]
        return " ".join(tokens)

    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for the input text."""
        return embedding_model.encode([text])[0]

    def store_faq_embeddings(self, faqs: List[Dict[str, str]], tenant_id: int):
        """Embed and store FAQs in the database with tenant association."""
        processed_faqs = [
            {
                "question": faq["question"],
                "answer": faq["answer"],
                "processed_question": self.preprocess_text(faq["question"]),
                "processed_answer": self.preprocess_text(faq["answer"]),
            }
            for faq in faqs
        ]

        for faq in processed_faqs:
            question_embedding = self.embed_text(faq["processed_question"])
            answer_embedding = self.embed_text(faq["processed_answer"])

            # Use DBInterface method to store FAQs
            self.db.add_faq(
                tenant_id,
                faq["question"],
                faq["answer"],
                pickle.dumps(question_embedding)
            )

    @lru_cache(maxsize=128)  # Cache results to speed up retrieval of frequently searched queries
    def load_faq_embeddings(self, tenant_id: int):
        """Load embeddings for a given tenant ID from the database."""
        faqs = self.db.get_faqs(tenant_id)  # Use DBInterface method to get FAQs
        question_embeddings = np.array([pickle.loads(faq["embedding"]) for faq in faqs])

        return faqs, question_embeddings

    def find_similar_faqs(self, query: str, tenant_id: int, top_k: int = 3) -> List[Dict[str, Any]]:
        """Find top similar FAQs for the given query."""
        processed_query = self.preprocess_text(query)
        query_embedding = self.embed_text(processed_query).reshape(1, -1)

        faqs, question_embeddings = self.load_faq_embeddings(tenant_id)
        self.index.add(question_embeddings)  # Add embeddings to FAISS index for in-memory search

        # Perform similarity search
        distances, indices = self.index.search(query_embedding, top_k)
        results = [
            {
                "question": faqs[i]["question"],
                "answer": faqs[i]["answer"],
                "distance": distances[0][j]
            }
            for j, i in enumerate(indices[0])
        ]

        # Clear index for next query (in-memory reset for different tenants or queries)
        self.index.reset()
        return results


class LLMHandler:
    @staticmethod
    def generate_llama_prompt(similar_faqs: List[Dict[str, Any]], user_query: str) -> str:
        """Generate prompt for LLM using similar FAQs."""
        context = "\n\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in similar_faqs])
        prompt = (
            f"You are a helpful and friendly customer support chatbot.\n"
            f"Use the following FAQ entries to provide an accurate answer to the user's question.\n\n"
            f"{context}\n\n"
            f"User Question: {user_query}\n\n"
            f"Answer based on the information above:"
        )
        return prompt

    @staticmethod
    def stream_llama_response(prompt: str, model: str = "llama3.2:1b", suffix: str = "") -> str:
        """Stream LLM response for a given prompt."""
        url = "http://localhost:11434/api/generate"  # Update with actual endpoint
        payload = {"model": model, "prompt": prompt, "suffix": suffix}

        try:
            response = requests.post(url, json=payload, stream=True)
            response.raise_for_status()

            # Stream response in chunks
            response_text = ""
            for chunk in response.iter_content(chunk_size=1024):
                decoded_chunk = chunk.decode('utf-8')
                response_text += decoded_chunk
                response_json = json.loads(decoded_chunk)
                generated_text = response_json.get("response", "")
                yield generated_text

        except requests.exceptions.RequestException as e:
            yield f"Error: {e}"
