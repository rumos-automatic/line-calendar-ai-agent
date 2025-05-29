"""
Secret Manager utilities
"""
import logging
from typing import Optional
from google.cloud import secretmanager

logger = logging.getLogger(__name__)


def get_secret(secret_id: str) -> Optional[str]:
    """
    Retrieve secret from Google Secret Manager
    
    Args:
        secret_id: Full resource name or short name of the secret
        
    Returns:
        Secret value as string, or None if error
    """
    try:
        client = secretmanager.SecretManagerServiceClient()
        
        # Access the secret version
        response = client.access_secret_version(request={"name": secret_id})
        
        # Return the decoded payload
        return response.payload.data.decode("UTF-8")
        
    except Exception as e:
        logger.error(f"Failed to retrieve secret {secret_id}: {e}")
        return None