"""
Tests for encryption utilities.
"""
import os
import pytest

# Set a test encryption key before importing the module
os.environ["ENCRYPTION_KEY"] = "test_encryption_key_for_testing_only"

from app.core.encryption import encrypt_tokens, decrypt_tokens


class TestEncryption:
    """Test encryption and decryption of tokens."""
    
    def test_encrypt_decrypt_round_trip(self):
        """Test that encrypting and decrypting returns the original tokens."""
        original_tokens = {
            "access_token": "ya29.example_access_token",
            "refresh_token": "1//example_refresh_token",
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "123456.apps.googleusercontent.com",
            "scopes": ["https://www.googleapis.com/auth/calendar.readonly"]
        }
        
        encrypted = encrypt_tokens(original_tokens)
        
        # Encrypted should be a non-empty string
        assert isinstance(encrypted, str)
        assert len(encrypted) > 0
        assert encrypted != str(original_tokens)
        
        # Decrypt should return original
        decrypted = decrypt_tokens(encrypted)
        assert decrypted == original_tokens
    
    def test_decrypt_invalid_token(self):
        """Test that decrypting invalid token returns None."""
        result = decrypt_tokens("not_a_valid_encrypted_token")
        assert result is None
    
    def test_decrypt_empty_token(self):
        """Test that decrypting empty token returns None."""
        result = decrypt_tokens("")
        assert result is None
        
        result = decrypt_tokens(None)
        assert result is None
    
    def test_encrypted_tokens_are_different_each_time(self):
        """Test that the same tokens produce different encrypted values (due to IV)."""
        tokens = {"access_token": "test_token"}
        
        encrypted1 = encrypt_tokens(tokens)
        encrypted2 = encrypt_tokens(tokens)
        
        # Fernet includes a timestamp, so same plaintext produces different ciphertext
        assert encrypted1 != encrypted2
        
        # But both should decrypt to the same value
        assert decrypt_tokens(encrypted1) == tokens
        assert decrypt_tokens(encrypted2) == tokens


def test_missing_encryption_key():
    """Test that missing ENCRYPTION_KEY raises an error."""
    # Save current key
    original_key = os.environ.get("ENCRYPTION_KEY")
    
    try:
        # Remove key
        if "ENCRYPTION_KEY" in os.environ:
            del os.environ["ENCRYPTION_KEY"]
        
        # Import fresh to test key missing
        import importlib
        import app.core.encryption as enc_module
        importlib.reload(enc_module)
        
        with pytest.raises(ValueError, match="ENCRYPTION_KEY"):
            enc_module.encrypt_tokens({"test": "data"})
    finally:
        # Restore key
        if original_key:
            os.environ["ENCRYPTION_KEY"] = original_key
