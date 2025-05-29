"""
Google Calendar service
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.services.auth_service import get_user_credentials

logger = logging.getLogger(__name__)


class CalendarService:
    """Google Calendar integration service"""
    
    async def add_event(
        self,
        line_user_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Add event to Google Calendar
        
        Args:
            line_user_id: LINE user ID
            entities: Parsed entities from NLP
            
        Returns:
            Result dict with status and message
        """
        try:
            credentials = await get_user_credentials(line_user_id)
            if not credentials:
                return {'success': False, 'message': '認証エラーが発生しました。'}
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Build event
            event = self._build_event_from_entities(entities)
            
            # Create event
            created_event = service.events().insert(
                calendarId='primary',
                body=event
            ).execute()
            
            logger.info(f"Created event {created_event['id']} for user {line_user_id}")
            
            return {
                'success': True,
                'message': f"予定「{event.get('summary', '')}」を追加しました。",
                'event_id': created_event['id']
            }
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {'success': False, 'message': 'カレンダーの更新に失敗しました。'}
        except Exception as e:
            logger.error(f"Error adding event: {e}")
            return {'success': False, 'message': 'エラーが発生しました。'}
    
    async def list_events(
        self,
        line_user_id: str,
        entities: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        List events from Google Calendar
        
        Args:
            line_user_id: LINE user ID
            entities: Parsed entities (date range, etc.)
            
        Returns:
            List of events
        """
        try:
            credentials = await get_user_credentials(line_user_id)
            if not credentials:
                return []
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # Determine date range
            start_date = entities.get('date', datetime.now().date())
            if 'start_date' in entities:
                start_date = entities['start_date']
            
            # Set time range
            time_min = datetime.combine(start_date, datetime.min.time()).isoformat() + 'Z'
            time_max = datetime.combine(start_date, datetime.max.time()).isoformat() + 'Z'
            
            # Get events
            events_result = service.events().list(
                calendarId='primary',
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Format events
            formatted_events = []
            for event in events:
                formatted_event = self._format_event(event)
                formatted_events.append(formatted_event)
            
            return formatted_events
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing events: {e}")
            return []
    
    async def delete_event(
        self,
        line_user_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Delete event from Google Calendar
        
        Args:
            line_user_id: LINE user ID
            entities: Parsed entities (event identifier)
            
        Returns:
            Result dict
        """
        try:
            credentials = await get_user_credentials(line_user_id)
            if not credentials:
                return {'success': False, 'message': '認証エラーが発生しました。'}
            
            service = build('calendar', 'v3', credentials=credentials)
            
            # For simplicity, find the first event today that matches criteria
            # In production, this would need better event identification
            events = await self.list_events(line_user_id, entities)
            
            if not events:
                return {'success': False, 'message': '削除する予定が見つかりませんでした。'}
            
            # Delete first matching event
            event_id = events[0].get('id')
            if event_id:
                service.events().delete(calendarId='primary', eventId=event_id).execute()
                return {'success': True, 'message': '予定を削除しました。'}
            
            return {'success': False, 'message': '予定の削除に失敗しました。'}
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {e}")
            return {'success': False, 'message': 'カレンダーの更新に失敗しました。'}
        except Exception as e:
            logger.error(f"Error deleting event: {e}")
            return {'success': False, 'message': 'エラーが発生しました。'}
    
    async def update_event(
        self,
        line_user_id: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update event in Google Calendar
        
        Args:
            line_user_id: LINE user ID
            entities: Parsed entities
            
        Returns:
            Result dict
        """
        # For initial release, redirect to delete + add
        # In production, implement proper event update logic
        return {'success': False, 'message': '予定の更新機能は開発中です。'}
    
    def _build_event_from_entities(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Build Google Calendar event from extracted entities"""
        event = {}
        
        # Set title
        event['summary'] = entities.get('title', '予定')
        
        # Set datetime
        if 'datetime' in entities:
            start_time = entities['datetime']
            end_time = start_time + timedelta(hours=1)  # Default 1 hour duration
        else:
            # Default to 9 AM today for 1 hour
            start_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1)
        
        event['start'] = {
            'dateTime': start_time.isoformat(),
            'timeZone': 'Asia/Tokyo'
        }
        event['end'] = {
            'dateTime': end_time.isoformat(),
            'timeZone': 'Asia/Tokyo'
        }
        
        # Set location
        if 'location' in entities:
            event['location'] = entities['location']
        
        return event
    
    def _format_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Format Google Calendar event for display"""
        formatted = {
            'id': event.get('id'),
            'title': event.get('summary', '(タイトルなし)'),
        }
        
        # Format start time
        start = event.get('start', {})
        if 'dateTime' in start:
            start_dt = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            formatted['start_time'] = start_dt.strftime('%H:%M')
        elif 'date' in start:
            formatted['start_time'] = '終日'
        
        # Format end time
        end = event.get('end', {})
        if 'dateTime' in end:
            end_dt = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
            formatted['end_time'] = end_dt.strftime('%H:%M')
        
        # Location
        if 'location' in event:
            formatted['location'] = event['location']
        
        return formatted