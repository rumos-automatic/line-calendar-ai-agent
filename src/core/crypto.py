"""
Cryptography utilities for token encryption
"""
from cryptography.fernet import Fernet
from src.core.config import settings
import base64
import logging

logger = logging.getLogger(__name__)


def get_encryption_key() -> bytes:
    """Get or generate encryption key"""
    if not settings.ENCRYPTION_KEY:
        raise ValueError("Encryption key not configured")
    
    # Ensure key is 32 bytes (Fernet requirement)
    key = settings.ENCRYPTION_KEY.encode()
    if len(key) != 32:
        # Pad or truncate to 32 bytes
        key = key[:32].ljust(32, b'0')
    
    return base64.urlsafe_b64encode(key)


def encrypt_token(token: str) -> str:
    """
    Encrypt a token
    
    Args:
        token: Plain text token
        
    Returns:
        Encrypted token as string
    """
    try:
        key = get_encryption_key()
        f = Fernet(key)
        encrypted = f.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a token
    
    Args:
        encrypted_token: Encrypted token string
        
    Returns:
        Decrypted token
    """
    try:
        key = get_encryption_key()
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise