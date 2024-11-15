# app/llm_integration.py
from transformers import pipeline

# Load model and pipeline
generator = pipeline("text-generation", model="gpt2")

def get_llm_response(prompt):
    result = generator(prompt, max_length=150, num_return_sequences=1)
    return result[0]["generated_text"]


def construct_prompt(similar_faqs, query):
    # Provide a prelude with the user query
    prompt = f"The user asked: {query}\n\n"
    prompt += "Based on similar questions in your FAQ, here are some relevant answers:\n\n"

    # Add each FAQ question and answer to the prompt
    for faq in similar_faqs:
        prompt += f"Q: {faq['question']}\nA: {faq['answer']}\n\n"

    # Closing note for the LLM to formulate a coherent response
    prompt += "Using this information, please answer the user's question accurately."

    return prompt
