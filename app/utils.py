import asyncio
import json
import secrets


def generate_api_key():
    return secrets.token_hex(16)  # Generate a secure 32-character hexadecimal API key


async def stream_words(text, delay=1):
    """
    Yields each word from the text with a delay between each, formatted for SSE.

    Parameters:
    - text (str): The text to be streamed word by word.
    - delay (int): Delay in seconds between each word. Default is 1 second.

    Yields:
    - str: The next word in an SSE format.
    """
    words = text.split()  # Split the text into words
    for word in words:
        await asyncio.sleep(delay)  # Simulate delay between words
        # Format each word in SSE data format
        yield f"data: {json.dumps(word +" ")}\n\n"
