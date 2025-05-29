"""
Reminder service for sending scheduled notifications
"""
from typing import List, Dict, Any
from datetime import datetime, time
import logging
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    PushMessageRequest,
    TextMessage,
    Configuration
)

from src.core.config import settings
from src.repositories.user_repository import UserRepository
from src.services.calendar_service import CalendarService

logger = logging.getLogger(__name__)

# LINE Bot API configuration
configuration = Configuration(
    host="https://api.line.me",
    access_token=settings.LINE_CHANNEL_ACCESS_TOKEN
)


async def send_reminder(line_user_id: str, message: str) -> bool:
    """
    Send reminder message to user
    
    Args:
        line_user_id: LINE user ID
        message: Reminder message
        
    Returns:
        True if successful
    """
    try:
        async with ApiClient(configuration=configuration) as api_client:
            api = MessagingApi(api_client)
            
            request = PushMessageRequest(
                to=line_user_id,
                messages=[TextMessage(text=message)]
            )
            
            await api.push_message(request)
            logger.info(f"Sent reminder to {line_user_id}")
            return True
            
    except Exception as e:
        logger.error(f"Failed to send reminder to {line_user_id}: {e}")
        return False


async def generate_reminders_for_all_users(time_slot: str) -> int:
    """
    Generate reminders for all eligible users
    
    Args:
        time_slot: 'morning' or 'evening'
        
    Returns:
        Number of reminders generated
    """
    try:
        user_repo = UserRepository()
        users = await user_repo.get_users_for_reminder(time_slot)
        
        count = 0
        calendar_service = CalendarService()
        
        for user in users:
            line_user_id = user['id']
            preferences = user.get('preferences', {})
            
            # Check if user wants reminders for this time slot
            reminder_time = None
            if time_slot == 'morning':
                reminder_time = preferences.get('reminder_time_morning', '09:00')
            elif time_slot == 'evening':
                reminder_time = preferences.get('reminder_time_evening', '21:00')
            
            if not reminder_time:
                continue
            
            # Generate reminder message
            message = await generate_reminder_message(
                line_user_id,
                preferences,
                calendar_service
            )
            
            if message:
                # In production, this would queue the task in Cloud Tasks
                # For now, send immediately
                success = await send_reminder(line_user_id, message)
                if success:
                    count += 1
        
        logger.info(f"Generated {count} reminders for {time_slot}")
        return count
        
    except Exception as e:
        logger.error(f"Error generating reminders: {e}")
        return 0


async def generate_reminder_message(
    line_user_id: str,
    preferences: Dict[str, Any],
    calendar_service: CalendarService
) -> str:
    """
    Generate reminder message for user
    
    Args:
        line_user_id: LINE user ID
        preferences: User preferences
        calendar_service: Calendar service instance
        
    Returns:
        Reminder message or None
    """
    try:
        days_ahead = preferences.get('reminder_days_ahead', 1)
        
        # Get events for the specified period
        entities = {
            'start_date': datetime.now().date(),
            'end_date': (datetime.now() + datetime.timedelta(days=days_ahead)).date()
        }
        
        events = await calendar_service.list_events(line_user_id, entities)
        
        if not events:
            return None  # No events, no reminder needed
        
        # Build reminder message
        if days_ahead == 1:
            message = "📅 明日の予定をお知らせします：\n\n"
        else:
            message = f"📅 今後{days_ahead}日間の予定をお知らせします：\n\n"
        
        for event in events[:5]:  # Limit to 5 events
            start_time = event.get('start_time', '')
            title = event.get('title', '(タイトルなし)')
            
            if start_time:
                message += f"• {start_time} {title}\n"
            else:
                message += f"• {title}\n"
        
        if len(events) > 5:
            message += f"\n... 他{len(events) - 5}件の予定があります"
        
        return message
        
    except Exception as e:
        logger.error(f"Error generating reminder message: {e}")
        return None