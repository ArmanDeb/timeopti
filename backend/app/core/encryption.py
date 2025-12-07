"""
Token encryption utilities for secure storage of OAuth tokens.

Uses Fernet symmetric encryption with a key derived from the ENCRYPTION_KEY 
environment variable. Tokens are encrypted before storage in the database
and decrypted when retrieved.
"""
import os
import json
import base64
import hashlib
from typing import Dict, Optional
from cryptography.fernet import Fernet, InvalidToken

def _get_fernet() -> Fernet:
    """
    Get a Fernet instance using the ENCRYPTION_KEY environment variable.
    The key is hashed to ensure it's the correct length for Fernet.
    """
    encryption_key = os.getenv("ENCRYPTION_KEY")
    
    if not encryption_key:
        raise ValueError(
            "ENCRYPTION_KEY environment variable is not set. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    
    # Hash the key to ensure it's exactly 32 bytes, then base64 encode for Fernet
    key_bytes = hashlib.sha256(encryption_key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(key_bytes)
    
    return Fernet(fernet_key)


def encrypt_tokens(tokens: Dict) -> str:
    """
    Encrypt a dictionary of tokens for secure storage.
    
    Args:
        tokens: Dictionary containing OAuth tokens (access_token, refresh_token, etc.)
        
    Returns:
        Base64-encoded encrypted string
    """
    fernet = _get_fernet()
    tokens_json = json.dumps(tokens)
    encrypted = fernet.encrypt(tokens_json.encode())
    return encrypted.decode()


def decrypt_tokens(encrypted_tokens: str) -> Optional[Dict]:
    """
    Decrypt an encrypted token string back to a dictionary.
    
    Args:
        encrypted_tokens: Base64-encoded encrypted string from encrypt_tokens()
        
    Returns:
        Dictionary containing OAuth tokens, or None if decryption fails
    """
    if not encrypted_tokens:
        return None
        
    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_tokens.encode())
        return json.loads(decrypted.decode())
    except InvalidToken:
        print("Warning: Failed to decrypt tokens - invalid token or key mismatch")
        return None
    except Exception as e:
        print(f"Warning: Failed to decrypt tokens - {e}")
        return None
