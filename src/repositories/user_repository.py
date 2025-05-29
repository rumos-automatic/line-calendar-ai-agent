"""
User repository for Firestore operations
"""
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from src.repositories.base_repository import BaseRepository
from src.core.crypto import encrypt_token, decrypt_token

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """Repository for user data"""
    
    def __init__(self):
        super().__init__('users')
    
    async def get_user(self, line_user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by LINE user ID"""
        return await self.get_by_id(line_user_id)
    
    async def create_user(
        self,
        line_user_id: str,
        google_email: str,
        refresh_token: str,
        token_expiry: datetime
    ) -> bool:
        """
        Create new user with Google credentials
        
        Args:
            line_user_id: LINE user ID
            google_email: Google account email
            refresh_token: Google refresh token (will be encrypted)
            token_expiry: Access token expiry time
            
        Returns:
            True if successful
        """
        try:
            # Encrypt refresh token
            encrypted_token = encrypt_token(refresh_token)
            
            data = {
                'google_email': google_email,
                'google_refresh_token_encrypted': encrypted_token,
                'google_token_expiry': token_expiry,
                'calendars_access': [],  # Will be populated later
                'preferences': {
                    'reminder_enabled': True,
                    'reminder_time_morning': '09:00',
                    'reminder_time_evening': '21:00',
                    'reminder_days_ahead': 1,
                    'reminder_before_event_minutes': 0
                },
                'is_active': True
            }
            
            return await self.create(line_user_id, data)
            
        except Exception as e:
            logger.error(f"Error creating user {line_user_id}: {e}")
            return False
    
    async def update_user_tokens(
        self,
        line_user_id: str,
        refresh_token: str,
        token_expiry: datetime
    ) -> bool:
        """Update user's Google tokens"""
        try:
            encrypted_token = encrypt_token(refresh_token)
            
            data = {
                'google_refresh_token_encrypted': encrypted_token,
                'google_token_expiry': token_expiry
            }
            
            return await self.update(line_user_id, data)
            
        except Exception as e:
            logger.error(f"Error updating tokens for {line_user_id}: {e}")
            return False
    
    async def get_user_refresh_token(self, line_user_id: str) -> Optional[str]:
        """Get decrypted refresh token for user"""
        user = await self.get_user(line_user_id)
        if not user or not user.get('google_refresh_token_encrypted'):
            return None
        
        try:
            return decrypt_token(user['google_refresh_token_encrypted'])
        except Exception as e:
            logger.error(f"Error decrypting token for {line_user_id}: {e}")
            return None
    
    async def update_user_preferences(
        self,
        line_user_id: str,
        preferences: Dict[str, Any]
    ) -> bool:
        """Update user preferences"""
        return await self.update(line_user_id, {'preferences': preferences})
    
    async def get_users_for_reminder(self, time_slot: str) -> list:
        """
        Get users who should receive reminders at specified time
        
        Args:
            time_slot: 'morning' or 'evening'
            
        Returns:
            List of users
        """
        # Query users with reminders enabled
        filters = [
            ('is_active', '==', True),
            ('preferences.reminder_enabled', '==', True)
        ]
        
        return await self.query(filters=filters)
    
    async def store_auth_state(
        self,
        state: str,
        data: Dict[str, Any],
        ttl_seconds: int = 600
    ) -> bool:
        """
        Store temporary auth state for PKCE flow
        
        Args:
            state: State parameter
            data: Data to store (line_user_id, code_verifier)
            ttl_seconds: Time to live in seconds
            
        Returns:
            True if successful
        """
        try:
            # Store in a separate collection with TTL
            auth_collection = self.db.collection('auth_states')
            doc_ref = auth_collection.document(state)
            
            data['expires_at'] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            doc_ref.set(data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error storing auth state: {e}")
            return False
    
    async def get_auth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Get and delete auth state"""
        try:
            auth_collection = self.db.collection('auth_states')
            doc_ref = auth_collection.document(state)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = doc.to_dict()
            
            # Check expiry
            if data.get('expires_at') and data['expires_at'] < datetime.utcnow():
                doc_ref.delete()
                return None
            
            # Delete after retrieval (one-time use)
            doc_ref.delete()
            
            return data
            
        except Exception as e:
            logger.error(f"Error getting auth state: {e}")
            return None