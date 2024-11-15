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
    def generate_llama_prompt(
            similar_faqs: List[Dict[str, Any]],
            user_query: str,
            conversation_history: List[Dict[str, str]] = []
    ) -> str:
        """Generate a focused prompt for the LLM using FAQs and conversation history for accurate, relevant responses."""

        # Concatenate Q&A pairs from similar FAQs to form the context
        faq_context = "\n\n".join([f"Q: {faq['question']}\nA: {faq['answer']}" for faq in similar_faqs])

        # Format the conversation history context
        conversation_context = "\n".join(
            [f"{message['role'].capitalize()}: {message['content']}" for message in conversation_history])

        # Structured and targeted prompt
        prompt = (
            f"You are A customer support chatbot, designed to give precise, relevant answers based on the provided FAQ. "
            f"Use the FAQ entries and conversation history below to craft a direct, helpful response to the user's question. "
            f"If the exact answer isn't in the FAQ, infer the best possible answer or advise on next steps.\n\n"

            f"FAQs:\n{faq_context}\n\n"
            f"Conversation so far:\n{conversation_context}\n\n"

            f"User question: {user_query}\n\n"

            f"Please provide a clear answer based on the information above. "
            f"Use a polite, concise tone and avoid unnecessary elaboration."
        )

        return prompt

    @staticmethod
    async def stream_llama_response(prompt: str, model: str = "llama3.2:1b", suffix: str = "") -> str:
        """Stream LLM response for a given prompt."""
        try:
            print(prompt)
            # Assuming AsyncClient.chat is asynchronous
            async for part in await AsyncClient().chat(
                    model= model,
                    messages=[{'role': 'user', 'content': prompt}],
                    stream=True
            ):
                # print(part['message']['content'], end='', flush=True)
                print(json.dumps(part['message']['content']))
                # yield response as json
                yield f"data: {json.dumps(part['message']['content'])}\n\n"
                # yield f"data: {part['message']['content']}"
        except Exception as e:
            yield f"data: Error occurred while streaming: {e}\n\n"
