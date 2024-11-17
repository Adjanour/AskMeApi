import asyncio
import json
import random
import secrets


def generate_api_key():
    return secrets.token_hex(16)  # Generate a secure 32-character hexadecimal API key



# Semaphore to limit concurrent streams
semaphore = asyncio.Semaphore(10)  # Adjust as needed for traffic

async def stream_words(text: str, delay: float = 1.0, min_words: int = 1, max_words: int = 3):
    """
    Streams chunks of words from the text with a delay between each chunk, formatted for SSE.

    Parameters:
        - text (str): The text to be streamed.
        - delay (float): Delay in seconds between chunks. Default is 1 second.
        - min_words (int): Minimum number of words in a chunk. Default is 1.
        - max_words (int): Maximum number of words in a chunk. Default is 3.

    Yields:
        - str: Chunks of words in SSE format.
    """
    words = text.split()  # Split the text into words
    idx = 0

    while idx < len(words):
        chunk_size = random.randint(min_words, max_words)  # Random chunk size
        chunk = words[idx:idx + chunk_size]  # Get a chunk of words
        idx += chunk_size  # Move the index forward

        # Yield the chunk in SSE format
        yield f"data: {' '.join(chunk)}\n\n"

        # Simulate delay between chunks
        await asyncio.sleep(delay)


async def safe_stream_words(text: str, delay: float = 1.0):
    """
    Wraps the stream_words function with a semaphore to limit concurrency and adds error handling.

    Parameters:
        - text (str): The text to be streamed.
        - delay (float): Delay in seconds between chunks. Default is 1 second.

    Yields:
        - str: Chunks of words in SSE format or an error message.
    """
    async with semaphore:  # Limit concurrent streams
        try:
            async for chunk in stream_words(text, delay):
                yield chunk
        except Exception as e:
            yield f"data: Error occurred during streaming: {str(e)}\n\n"
