import secrets
import hashlib
from typing import Optional


def generate_secure_token(length: int = 32) -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(length)


def hash_secret(secret: str, salt: Optional[str] = None) -> str:
    """Hash a secret with optional salt using SHA-256"""
    if salt is None:
        salt = secrets.token_hex(16)
    
    # Combine the secret and salt
    salted_secret = secret + salt
    
    # Hash the salted secret
    hashed = hashlib.sha256(salted_secret.encode()).hexdigest()
    
    # Return the hash with the salt prepended (format: salt:hash)
    return f"{salt}:{hashed}"


def verify_hash(secret: str, hashed_secret: str) -> bool:
    """Verify a secret against a hashed value"""
    try:
        salt, stored_hash = hashed_secret.split(":", 1)
        return hash_secret(secret, salt) == hashed_secret
    except ValueError:
        # If the format is incorrect, return False
        return False


def is_valid_api_key_format(api_key: str) -> bool:
    """Validate the format of an API key"""
    # API keys are typically long strings with specific patterns
    # For example, OpenAI keys start with "sk-" and are ~51 characters long
    # Cohere keys are typically 40+ alphanumeric characters
    
    if not api_key or len(api_key) < 20:
        return False
    
    # Check for common API key patterns
    if api_key.startswith("sk-") and len(api_key) >= 50:  # OpenAI style
        return True
    elif len(api_key) >= 40 and api_key.isalnum():  # Generic alphanumeric
        return True
    elif len(api_key) >= 32 and all(c.isalnum() or c in "-_" for c in api_key):  # With special chars
        return True
    
    return False