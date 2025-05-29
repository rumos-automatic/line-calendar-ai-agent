"""
Cloud Tasks endpoints for async processing
"""
from fastapi import APIRouter, Request, HTTPException
from typing import Dict, Any
import logging

from src.services.reminder_service import send_reminder
from src.services.auth_service import refresh_user_token

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/reminder")
async def process_reminder(request: Request):
    """
    Process reminder task from Cloud Tasks
    """
    try:
        payload = await request.json()
        line_user_id = payload.get("line_user_id")
        message = payload.get("message")
        
        if not line_user_id or not message:
            raise ValueError("Missing required fields")
        
        # Send reminder
        await send_reminder(line_user_id, message)
        
        return {"status": "sent"}
        
    except Exception as e:
        logger.error(f"Failed to process reminder: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh-token")
async def process_token_refresh(request: Request):
    """
    Refresh user's Google token
    """
    try:
        payload = await request.json()
        line_user_id = payload.get("line_user_id")
        
        if not line_user_id:
            raise ValueError("Missing LINE user ID")
        
        # Refresh token
        await refresh_user_token(line_user_id)
        
        return {"status": "refreshed"}
        
    except Exception as e:
        logger.error(f"Failed to refresh token: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-reminders")
async def generate_daily_reminders(request: Request):
    """
    Generate reminders for all users
    Called by Cloud Scheduler
    """
    try:
        payload = await request.json()
        time_slot = payload.get("time_slot", "morning")  # morning or evening
        
        from src.services.reminder_service import generate_reminders_for_all_users
        count = await generate_reminders_for_all_users(time_slot)
        
        return {"status": "generated", "count": count}
        
    except Exception as e:
        logger.error(f"Failed to generate reminders: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/proactive-suggestions")
async def generate_proactive_suggestions(request: Request):
    """
    Generate proactive suggestions for users
    Called by Cloud Scheduler
    """
    try:
        from src.services.conversation_service import ConversationService
        from src.repositories.user_repository import UserRepository
        from linebot.v3.messaging import (
            ApiClient,
            MessagingApi,
            PushMessageRequest,
            TextMessage,
            Configuration
        )
        from src.core.config import settings
        
        # Only process if AI is enabled
        if not settings.USE_AI_AGENT or not settings.OPENAI_API_KEY:
            return {"status": "skipped", "reason": "AI agent not enabled"}
        
        conversation_service = ConversationService()
        user_repo = UserRepository()
        
        # Get active users
        users = await user_repo.query(
            filters=[('is_active', '==', True)],
            limit=100  # Process in batches
        )
        
        # LINE API configuration
        configuration = Configuration(
            host="https://api.line.me",
            access_token=settings.LINE_CHANNEL_ACCESS_TOKEN
        )
        
        count = 0
        
        async with ApiClient(configuration=configuration) as api_client:
            api = MessagingApi(api_client)
            
            for user in users:
                line_user_id = user['id']
                
                # Generate suggestions
                suggestions = await conversation_service.get_proactive_suggestions(
                    line_user_id
                )
                
                if suggestions:
                    # Send suggestions
                    try:
                        request = PushMessageRequest(
                            to=line_user_id,
                            messages=[TextMessage(text=f"💡 提案：\n{suggestions}")]
                        )
                        await api.push_message(request)
                        count += 1
                    except Exception as e:
                        logger.error(f"Failed to send suggestion to {line_user_id}: {e}")
        
        return {"status": "sent", "count": count}
        
    except Exception as e:
        logger.error(f"Failed to generate proactive suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset-ai-usage")
async def reset_monthly_ai_usage(request: Request):
    """
    Reset monthly AI usage counters
    Called by Cloud Scheduler monthly
    """
    try:
        from src.repositories.user_repository import UserRepository
        from datetime import datetime, timedelta
        
        user_repo = UserRepository()
        
        # Get all users
        users = await user_repo.query(limit=1000)
        
        count = 0
        for user in users:
            subscription = user.get('subscription', {})
            last_reset = subscription.get('last_reset_at')
            
            # Check if reset is needed (30 days since last reset)
            should_reset = False
            if last_reset:
                last_reset_date = datetime.fromisoformat(last_reset)
                if datetime.now() - last_reset_date >= timedelta(days=30):
                    should_reset = True
            else:
                should_reset = True
            
            if should_reset:
                subscription['ai_calls_used'] = 0
                subscription['last_reset_at'] = datetime.now().isoformat()
                
                success = await user_repo.update(user['id'], {
                    'subscription': subscription
                })
                
                if success:
                    count += 1
        
        logger.info(f"Reset AI usage for {count} users")
        return {"status": "reset", "count": count}
        
    except Exception as e:
        logger.error(f"Failed to reset AI usage: {e}")
        raise HTTPException(status_code=500, detail=str(e))