"""
LIFF (LINE Front-end Framework) endpoints
"""
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
import logging
import secrets
import hashlib
import base64

from src.core.config import settings
from src.services.auth_service import (
    generate_google_auth_url,
    exchange_code_for_tokens,
    save_user_tokens
)
from src.repositories.user_repository import UserRepository

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/auth/google")
async def start_google_auth(line_user_id: str):
    """
    Start Google OAuth flow with PKCE
    """
    if not line_user_id:
        raise HTTPException(status_code=400, detail="Missing LINE user ID")
    
    # Generate PKCE parameters
    code_verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode('utf-8').rstrip('=')
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store PKCE verifier and LINE user ID with state (temporary storage)
    # In production, store in Firestore with TTL
    user_repo = UserRepository()
    await user_repo.store_auth_state(state, {
        'line_user_id': line_user_id,
        'code_verifier': code_verifier
    })
    
    # Generate auth URL
    auth_url = generate_google_auth_url(state, code_challenge)
    
    return RedirectResponse(url=auth_url)


@router.get("/status")
async def get_user_status(line_user_id: str):
    """
    Get user's connection status
    """
    if not line_user_id:
        raise HTTPException(status_code=400, detail="Missing LINE user ID")
    
    user_repo = UserRepository()
    user = await user_repo.get_user(line_user_id)
    
    return {
        "linked": user is not None and user.get("google_email") is not None,
        "email": user.get("google_email") if user else None
    }


@router.get("/settings")
async def get_user_settings(line_user_id: str):
    """
    Get user's reminder settings and subscription info
    """
    if not line_user_id:
        raise HTTPException(status_code=400, detail="Missing LINE user ID")
    
    user_repo = UserRepository()
    user = await user_repo.get_user(line_user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = user.get("preferences", {})
    subscription = user.get("subscription", {})
    
    # Get subscription service info
    from src.services.subscription_service import SubscriptionService
    subscription_service = SubscriptionService()
    subscription_info = await subscription_service.get_subscription_info(line_user_id)
    
    return {
        "reminder_enabled": preferences.get("reminder_enabled", False),
        "reminder_time_morning": preferences.get("reminder_time_morning", "09:00"),
        "reminder_time_evening": preferences.get("reminder_time_evening", "21:00"),
        "reminder_days_ahead": preferences.get("reminder_days_ahead", 1),
        "use_ai_agent": preferences.get("use_ai_agent", False),
        "subscription": subscription_info
    }


@router.post("/settings")
async def update_user_settings(line_user_id: str, settings: dict):
    """
    Update user's reminder settings
    """
    if not line_user_id:
        raise HTTPException(status_code=400, detail="Missing LINE user ID")
    
    user_repo = UserRepository()
    await user_repo.update_user_preferences(line_user_id, settings)
    
    return {"status": "updated"}


@router.post("/upgrade-plan")
async def upgrade_user_plan(line_user_id: str, plan: str):
    """
    Upgrade user's subscription plan
    """
    if not line_user_id:
        raise HTTPException(status_code=400, detail="Missing LINE user ID")
    
    if plan not in ['basic', 'premium']:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    from src.services.subscription_service import SubscriptionService
    subscription_service = SubscriptionService()
    
    result = await subscription_service.upgrade_plan(line_user_id, plan)
    
    if result['success']:
        return result
    else:
        raise HTTPException(status_code=400, detail=result['message'])