"""
Japanese datetime parsing for natural language input
"""
import re
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, time
import logging

logger = logging.getLogger(__name__)


class DateTimeParser:
    """Parse Japanese datetime expressions"""
    
    def __init__(self):
        self.weekdays = {
            '月': 0, '火': 1, '水': 2, '木': 3, '金': 4, '土': 5, '日': 6,
            '月曜': 0, '火曜': 1, '水曜': 2, '木曜': 3, '金曜': 4, '土曜': 5, '日曜': 6
        }
        
        self.time_patterns = [
            r'(\d+)時(\d+)?分?',  # 15時30分, 15時
            r'(\d+):(\d+)',       # 15:30
            r'午前(\d+)時(\d+)?分?',  # 午前10時30分
            r'午後(\d+)時(\d+)?分?',  # 午後3時30分
        ]
    
    def parse(self, text: str) -> Dict[str, Any]:
        """
        Parse datetime from Japanese text
        
        Args:
            text: Input text
            
        Returns:
            Dict with datetime information
        """
        result = {}
        
        # Parse date
        date_info = self._parse_date(text)
        if date_info:
            result.update(date_info)
        
        # Parse time
        time_info = self._parse_time(text)
        if time_info:
            result.update(time_info)
        
        # Combine date and time if both exist
        if 'date' in result and 'time' in result:
            result['datetime'] = datetime.combine(result['date'], result['time'])
        elif 'date' in result:
            # Default to 9:00 AM if only date is specified
            result['datetime'] = datetime.combine(result['date'], time(9, 0))
        
        return result
    
    def _parse_date(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse date expressions"""
        now = datetime.now()
        
        # Today/Tomorrow patterns
        if '今日' in text:
            return {'date': now.date()}
        elif '明日' in text:
            return {'date': (now + timedelta(days=1)).date()}
        elif '明後日' in text:
            return {'date': (now + timedelta(days=2)).date()}
        elif '昨日' in text:
            return {'date': (now - timedelta(days=1)).date()}
        
        # Weekday patterns
        weekday_match = self._parse_weekday(text)
        if weekday_match:
            return weekday_match
        
        # Specific date patterns (MM/DD, MM月DD日)
        date_match = self._parse_specific_date(text)
        if date_match:
            return date_match
        
        # Relative patterns (来週、今週、etc.)
        relative_match = self._parse_relative_date(text)
        if relative_match:
            return relative_match
        
        return None
    
    def _parse_time(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse time expressions"""
        
        for pattern in self.time_patterns:
            match = re.search(pattern, text)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if len(match.groups()) > 1 and match.group(2) else 0
                
                # Handle afternoon/evening
                if '午後' in pattern and hour < 12:
                    hour += 12
                elif '午前' in pattern and hour == 12:
                    hour = 0
                
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return {'time': time(hour, minute)}
        
        # Named time periods
        if '朝' in text or '午前' in text:
            return {'time': time(9, 0)}
        elif '昼' in text:
            return {'time': time(12, 0)}
        elif '午後' in text:
            return {'time': time(15, 0)}
        elif '夕方' in text:
            return {'time': time(18, 0)}
        elif '夜' in text:
            return {'time': time(20, 0)}
        
        return None
    
    def _parse_weekday(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse weekday references"""
        now = datetime.now()
        current_weekday = now.weekday()
        
        for day_name, weekday in self.weekdays.items():
            if day_name in text:
                days_ahead = weekday - current_weekday
                
                # Handle next week
                if '来週' in text or days_ahead <= 0:
                    days_ahead += 7
                
                target_date = (now + timedelta(days=days_ahead)).date()
                return {'date': target_date}
        
        return None
    
    def _parse_specific_date(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse specific dates like MM月DD日 or MM/DD"""
        now = datetime.now()
        
        # MM月DD日 pattern
        match = re.search(r'(\d+)月(\d+)日', text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            
            try:
                # Try current year first
                target_date = datetime(now.year, month, day).date()
                
                # If date is in the past, use next year
                if target_date < now.date():
                    target_date = datetime(now.year + 1, month, day).date()
                
                return {'date': target_date}
            except ValueError:
                pass
        
        # MM/DD pattern
        match = re.search(r'(\d+)/(\d+)', text)
        if match:
            month = int(match.group(1))
            day = int(match.group(2))
            
            try:
                target_date = datetime(now.year, month, day).date()
                
                if target_date < now.date():
                    target_date = datetime(now.year + 1, month, day).date()
                
                return {'date': target_date}
            except ValueError:
                pass
        
        return None
    
    def _parse_relative_date(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse relative date expressions"""
        now = datetime.now()
        
        if '来週' in text:
            # Next Monday
            days_ahead = 7 - now.weekday()
            return {'date': (now + timedelta(days=days_ahead)).date()}
        elif '今週' in text:
            # This Monday
            days_back = now.weekday()
            return {'date': (now - timedelta(days=days_back)).date()}
        elif '来月' in text:
            # First day of next month
            if now.month == 12:
                next_month = datetime(now.year + 1, 1, 1)
            else:
                next_month = datetime(now.year, now.month + 1, 1)
            return {'date': next_month.date()}
        
        return None