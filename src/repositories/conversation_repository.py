"""
Conversation history repository for Firestore
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from google.cloud import firestore

from src.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class ConversationRepository(BaseRepository):
    """Repository for conversation history"""
    
    def __init__(self):
        super().__init__('conversations')
    
    async def add_message(
        self,
        line_user_id: str,
        role: str,
        content: str,
        function_call: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a message to conversation history
        
        Args:
            line_user_id: LINE user ID
            role: Message role (user/assistant/function)
            content: Message content
            function_call: Function call data if any
            metadata: Additional metadata
            
        Returns:
            True if successful
        """
        try:
            # Create conversation document ID (user_id + timestamp)
            doc_id = f"{line_user_id}_{datetime.utcnow().timestamp()}"
            
            data = {
                'line_user_id': line_user_id,
                'role': role,
                'content': content,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'metadata': metadata or {}
            }
            
            if function_call:
                data['function_call'] = function_call
            
            return await self.create(doc_id, data)
            
        except Exception as e:
            logger.error(f"Error adding conversation message: {e}")
            return False
    
    async def get_conversation_history(
        self,
        line_user_id: str,
        limit: int = 10,
        hours_back: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get recent conversation history for a user
        
        Args:
            line_user_id: LINE user ID
            limit: Maximum number of messages to return
            hours_back: How many hours back to look
            
        Returns:
            List of conversation messages
        """
        try:
            # Calculate time threshold
            time_threshold = datetime.utcnow() - timedelta(hours=hours_back)
            
            # Query messages
            filters = [
                ('line_user_id', '==', line_user_id),
                ('timestamp', '>=', time_threshold)
            ]
            
            messages = await self.query(
                filters=filters,
                order_by='timestamp',
                limit=limit
            )
            
            return messages
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []
    
    async def get_last_mentioned_event(
        self,
        line_user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get the last event mentioned in conversation
        
        Args:
            line_user_id: LINE user ID
            
        Returns:
            Event data or None
        """
        try:
            # Get recent messages with event metadata
            messages = await self.get_conversation_history(
                line_user_id,
                limit=20,
                hours_back=2
            )
            
            # Look for messages with event metadata
            for message in reversed(messages):
                metadata = message.get('metadata', {})
                if 'event' in metadata:
                    return metadata['event']
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting last mentioned event: {e}")
            return None
    
    async def clear_old_conversations(self, days_to_keep: int = 7) -> int:
        """
        Clear old conversation history
        
        Args:
            days_to_keep: Number of days to keep
            
        Returns:
            Number of deleted messages
        """
        try:
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            
            # Query old messages
            filters = [('timestamp', '<', cutoff_date)]
            old_messages = await self.query(filters=filters)
            
            # Delete old messages
            count = 0
            for message in old_messages:
                if await self.delete(message['id']):
                    count += 1
            
            logger.info(f"Deleted {count} old conversation messages")
            return count
            
        except Exception as e:
            logger.error(f"Error clearing old conversations: {e}")
            return 0
    
    async def get_conversation_context(
        self,
        line_user_id: str
    ) -> Dict[str, Any]:
        """
        Get conversation context for AI processing
        
        Args:
            line_user_id: LINE user ID
            
        Returns:
            Context dictionary
        """
        try:
            # Get recent conversation
            messages = await self.get_conversation_history(
                line_user_id,
                limit=10,
                hours_back=2
            )
            
            # Get last mentioned event
            last_event = await self.get_last_mentioned_event(line_user_id)
            
            # Format for AI
            formatted_messages = []
            for msg in messages:
                formatted = {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", "")
                }
                if msg.get("function_call"):
                    formatted["function_call"] = msg["function_call"]
                
                formatted_messages.append(formatted)
            
            return {
                "messages": formatted_messages,
                "last_event": last_event,
                "user_id": line_user_id
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return {
                "messages": [],
                "last_event": None,
                "user_id": line_user_id
            }