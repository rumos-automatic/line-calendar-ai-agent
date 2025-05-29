"""
User data models
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime


class UserPreferences(BaseModel):
    """User preferences model"""
    reminder_enabled: bool = True
    reminder_time_morning: str = "09:00"
    reminder_time_evening: str = "21:00"
    reminder_days_ahead: int = 1
    reminder_before_event_minutes: int = 0
    use_ai_agent: bool = False  # User-specific AI mode setting


class SubscriptionStatus(BaseModel):
    """User subscription status"""
    plan: str = "free"  # free, basic, premium
    is_active: bool = True
    expires_at: Optional[datetime] = None
    ai_calls_used: int = 0
    ai_calls_limit: int = 10  # Monthly limit for free plan
    last_reset_at: Optional[datetime] = None


class User(BaseModel):
    """User model for Firestore"""
    line_user_id: str
    google_email: Optional[EmailStr] = None
    google_refresh_token_encrypted: Optional[str] = None
    google_token_expiry: Optional[datetime] = None
    calendars_access: list[str] = []
    preferences: UserPreferences = UserPreferences()
    subscription: SubscriptionStatus = SubscriptionStatus()
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuthState(BaseModel):
    """Temporary auth state for PKCE flow"""
    line_user_id: str
    code_verifier: str
    expires_at: datetime