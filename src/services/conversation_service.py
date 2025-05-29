"""
Conversation management service
"""
from typing import Dict, Any, List, Optional
import logging

from src.repositories.conversation_repository import ConversationRepository
from src.agents.calendar_agent import CalendarAgent

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for managing conversations with context"""
    
    def __init__(self):
        self.conversation_repo = ConversationRepository()
        self.calendar_agent = CalendarAgent()
    
    async def process_message_with_ai(
        self,
        line_user_id: str,
        message: str
    ) -> str:
        """
        Process message with AI agent and conversation context
        
        Args:
            line_user_id: LINE user ID
            message: User's message
            
        Returns:
            AI response
        """
        try:
            # Save user message
            await self.conversation_repo.add_message(
                line_user_id=line_user_id,
                role="user",
                content=message
            )
            
            # Get conversation context
            context = await self.conversation_repo.get_conversation_context(line_user_id)
            
            # Process with AI
            response, function_results = await self.calendar_agent.process_message(
                user_id=line_user_id,
                message=message,
                conversation_history=context.get("messages", [])
            )
            
            # Save AI response
            await self.conversation_repo.add_message(
                line_user_id=line_user_id,
                role="assistant",
                content=response,
                metadata={
                    "function_results": function_results
                } if function_results else None
            )
            
            # If there were function results with events, save them for context
            for result in function_results:
                if "event" in result:
                    await self._save_event_context(line_user_id, result["event"])
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message with AI: {e}")
            return "申し訳ございません。処理中にエラーが発生しました。"
    
    async def _save_event_context(
        self,
        line_user_id: str,
        event: Dict[str, Any]
    ):
        """Save event information for context"""
        try:
            await self.conversation_repo.add_message(
                line_user_id=line_user_id,
                role="system",
                content=f"Event referenced: {event.get('title', 'Unknown')}",
                metadata={"event": event}
            )
        except Exception as e:
            logger.error(f"Error saving event context: {e}")
    
    async def get_proactive_suggestions(
        self,
        line_user_id: str
    ) -> Optional[str]:
        """
        Generate proactive suggestions based on user's calendar
        
        Args:
            line_user_id: LINE user ID
            
        Returns:
            Suggestion message or None
        """
        try:
            from src.services.calendar_service import CalendarService
            from datetime import datetime, timedelta
            
            calendar_service = CalendarService()
            
            # Get today's and tomorrow's events
            today_entities = {"date": datetime.now().date()}
            tomorrow_entities = {"date": (datetime.now() + timedelta(days=1)).date()}
            
            today_events = await calendar_service.list_events(line_user_id, today_entities)
            tomorrow_events = await calendar_service.list_events(line_user_id, tomorrow_entities)
            
            suggestions = []
            
            # Check for busy days
            if len(today_events) >= 5:
                suggestions.append("今日は予定が多いですね。休憩時間を確保することをお勧めします。")
            
            # Check for early morning meetings
            for event in tomorrow_events:
                start_time = event.get("start_time", "")
                if start_time and start_time < "09:00":
                    suggestions.append(f"明日は{start_time}から予定があります。早めに休むことをお勧めします。")
                    break
            
            # Check for consecutive meetings
            if len(today_events) >= 2:
                consecutive = self._check_consecutive_meetings(today_events)
                if consecutive:
                    suggestions.append("連続した会議があります。間に休憩を入れることを検討してください。")
            
            return "\n".join(suggestions) if suggestions else None
            
        except Exception as e:
            logger.error(f"Error generating proactive suggestions: {e}")
            return None
    
    def _check_consecutive_meetings(self, events: List[Dict[str, Any]]) -> bool:
        """Check if there are consecutive meetings without breaks"""
        if len(events) < 2:
            return False
        
        # Sort events by start time
        sorted_events = sorted(events, key=lambda x: x.get("start_time", ""))
        
        for i in range(len(sorted_events) - 1):
            current_end = sorted_events[i].get("end_time", "")
            next_start = sorted_events[i + 1].get("start_time", "")
            
            if current_end and next_start and current_end >= next_start:
                return True
        
        return False