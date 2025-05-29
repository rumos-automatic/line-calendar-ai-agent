"""
Firestore database connection and utilities
"""
import logging
from typing import Optional
from google.cloud import firestore
from google.auth import credentials
import google.auth

logger = logging.getLogger(__name__)


class FirestoreClient:
    """Singleton Firestore client"""
    
    _instance: Optional['FirestoreClient'] = None
    _db: Optional[firestore.Client] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @property
    def db(self) -> firestore.Client:
        """Get Firestore client instance"""
        if self._db is None:
            self._db = self._create_client()
        return self._db
    
    def _create_client(self) -> firestore.Client:
        """Create Firestore client"""
        try:
            from src.core.config import settings
            
            # For Vercel deployment, use service account key
            if settings.ENVIRONMENT == "production" and hasattr(settings, 'GOOGLE_SERVICE_ACCOUNT_KEY'):
                import json
                from google.oauth2 import service_account
                
                # Parse service account key from environment variable
                service_account_info = json.loads(settings.GOOGLE_SERVICE_ACCOUNT_KEY)
                credentials = service_account.Credentials.from_service_account_info(
                    service_account_info
                )
                return firestore.Client(
                    project=settings.GOOGLE_CLOUD_PROJECT,
                    credentials=credentials
                )
            else:
                # In development, use ADC or emulator
                return firestore.Client(project=settings.GOOGLE_CLOUD_PROJECT)
        except Exception as e:
            logger.error(f"Failed to create Firestore client: {e}")
            raise


# Global instance
firestore_client = FirestoreClient()


def get_db() -> firestore.Client:
    """
    Dependency to get Firestore database instance
    
    Returns:
        Firestore client
    """
    return firestore_client.db