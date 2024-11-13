import secrets


def generate_api_key():
    return secrets.token_hex(16)  # Generate a secure 32-character hexadecimal API key
