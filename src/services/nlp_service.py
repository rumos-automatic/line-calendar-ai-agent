"""
Natural Language Processing service (Pattern-based for initial release)
"""
import re
from typing import Tuple, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

from src.nlp.datetime_parser import DateTimeParser
from src.nlp.intent_classifier import IntentClassifier

logger = logging.getLogger(__name__)


class NLPService:
    """Natural Language Processing service"""
    
    def __init__(self):
        self.datetime_parser = DateTimeParser()
        self.intent_classifier = IntentClassifier()
    
    async def process_message(self, message: str) -> Tuple[str, Dict[str, Any]]:
        """
        Process message and extract intent and entities
        
        Args:
            message: Input message text
            
        Returns:
            Tuple of (intent, entities)
        """
        try:
            # Clean message
            message = message.strip()
            
            # Classify intent
            intent = self.intent_classifier.classify(message)
            
            # Extract entities based on intent
            entities = {}
            
            if intent in ['add_event', 'update_event']:
                entities.update(self._extract_event_entities(message))
            elif intent in ['list_events', 'delete_event']:
                entities.update(self._extract_query_entities(message))
            
            logger.info(f"NLP processed: '{message}' -> Intent: {intent}, Entities: {entities}")
            
            return intent, entities
            
        except Exception as e:
            logger.error(f"NLP processing failed: {e}")
            return "unknown", {}
    
    def _extract_event_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for event creation/update"""
        entities = {}
        
        # Extract datetime
        datetime_info = self.datetime_parser.parse(message)
        if datetime_info:
            entities.update(datetime_info)
        
        # Extract title (simple heuristic)
        title = self._extract_title(message)
        if title:
            entities['title'] = title
        
        # Extract location (if mentioned)
        location = self._extract_location(message)
        if location:
            entities['location'] = location
        
        return entities
    
    def _extract_query_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities for queries"""
        entities = {}
        
        # Extract date range for listing events
        datetime_info = self.datetime_parser.parse(message)
        if datetime_info:
            entities.update(datetime_info)
        else:
            # Default to today if no date specified
            entities['start_date'] = datetime.now().date()
            entities['end_date'] = datetime.now().date()
        
        return entities
    
    def _extract_title(self, message: str) -> Optional[str]:
        """Extract event title from message"""
        # Remove common datetime expressions
        clean_message = re.sub(r'(明日|今日|明後日|来週|今週|来月|今月)', '', message)
        clean_message = re.sub(r'(\d+時|\d+:\d+|\d+分)', '', clean_message)
        clean_message = re.sub(r'(午前|午後|朝|昼|夜|夕方)', '', clean_message)
        clean_message = re.sub(r'(月曜|火曜|水曜|木曜|金曜|土曜|日曜)日?', '', clean_message)
        clean_message = re.sub(r'\d+月\d+日', '', clean_message)
        
        # Remove intent keywords
        clean_message = re.sub(r'(追加|作成|登録|予定|スケジュール|に|を|で|から|まで)', '', clean_message)
        
        # Clean up
        title = clean_message.strip()
        
        if len(title) > 2:  # Minimum length check
            return title
        
        return None
    
    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location from message"""
        # Look for location indicators
        location_patterns = [
            r'で\s*(.+?)(?:で|に|を|$)',  # "〜で"
            r'にて\s*(.+?)(?:で|に|を|$)',  # "〜にて"
            r'@\s*(.+?)(?:\s|$)',  # "@location"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message)
            if match:
                location = match.group(1).strip()
                if len(location) > 1:
                    return location
        
        return None