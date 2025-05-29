"""
Authentication service for Google OAuth
"""
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import logging
from urllib.parse import urlencode
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from src.core.config import settings
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)

# OAuth 2.0 scopes
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/userinfo.email'
]


def generate_google_auth_url(state: str, code_challenge: str) -> str:
    """
    Generate Google OAuth URL with PKCE
    
    Args:
        state: State parameter for CSRF protection
        code_challenge: PKCE code challenge
        
    Returns:
        Authorization URL
    """
    params = {
        'client_id': settings.GOOGLE_CLIENT_ID,
        'redirect_uri': settings.GOOGLE_REDIRECT_URI,
        'response_type': 'code',
        'scope': ' '.join(SCOPES),
        'access_type': 'offline',
        'prompt': 'consent',
        'state': state,
        'code_challenge': code_challenge,
        'code_challenge_method': 'S256'
    }
    
    base_url = 'https://accounts.google.com/o/oauth2/v2/auth'
    return f"{base_url}?{urlencode(params)}"


async def exchange_code_for_tokens(
    code: str,
    code_verifier: str
) -> Dict[str, Any]:
    """
    Exchange authorization code for tokens
    
    Args:
        code: Authorization code from Google
        code_verifier: PKCE code verifier
        
    Returns:
        Dict with tokens and user info
    """
    try:
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                }
            },
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        # Exchange code for tokens with PKCE
        flow.fetch_token(
            code=code,
            code_verifier=code_verifier
        )
        
        credentials = flow.credentials
        
        # Get user info
        service = build('oauth2', 'v2', credentials=credentials)
        user_info = service.userinfo().get().execute()
        
        return {
            'refresh_token': credentials.refresh_token,
            'access_token': credentials.token,
            'token_expiry': credentials.expiry,
            'email': user_info.get('email')
        }
        
    except Exception as e:
        logger.error(f"Failed to exchange code for tokens: {e}")
        raise


async def save_user_tokens(
    line_user_id: str,
    tokens: Dict[str, Any]
) -> bool:
    """
    Save user tokens to database
    
    Args:
        line_user_id: LINE user ID
        tokens: Token data from Google
        
    Returns:
        True if successful
    """
    try:
        user_repo = UserRepository()
        
        # Check if user exists
        existing_user = await user_repo.get_user(line_user_id)
        
        if existing_user:
            # Update existing user
            return await user_repo.update_user_tokens(
                line_user_id,
                tokens['refresh_token'],
                tokens['token_expiry']
            )
        else:
            # Create new user
            return await user_repo.create_user(
                line_user_id,
                tokens['email'],
                tokens['refresh_token'],
                tokens['token_expiry']
            )
            
    except Exception as e:
        logger.error(f"Failed to save user tokens: {e}")
        return False


async def get_user_credentials(line_user_id: str) -> Optional[Credentials]:
    """
    Get valid Google credentials for user
    
    Args:
        line_user_id: LINE user ID
        
    Returns:
        Google credentials or None
    """
    try:
        user_repo = UserRepository()
        user = await user_repo.get_user(line_user_id)
        
        if not user:
            return None
        
        # Get decrypted refresh token
        refresh_token = await user_repo.get_user_refresh_token(line_user_id)
        if not refresh_token:
            return None
        
        # Create credentials
        credentials = Credentials(
            token=None,  # Will be refreshed
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=SCOPES
        )
        
        # Refresh if needed
        if not credentials.valid:
            credentials.refresh(Request())
            
            # Update token expiry in database
            await user_repo.update_user_tokens(
                line_user_id,
                refresh_token,
                credentials.expiry
            )
        
        return credentials
        
    except Exception as e:
        logger.error(f"Failed to get user credentials: {e}")
        return None


async def refresh_user_token(line_user_id: str) -> bool:
    """
    Refresh user's Google token
    
    Args:
        line_user_id: LINE user ID
        
    Returns:
        True if successful
    """
    try:
        credentials = await get_user_credentials(line_user_id)
        return credentials is not None
        
    except Exception as e:
        logger.error(f"Failed to refresh token for {line_user_id}: {e}")
        return False