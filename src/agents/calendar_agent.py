"""
Calendar Agent using OpenAI function calling
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
from openai import AsyncOpenAI

from src.core.config import settings
from src.services.calendar_service import CalendarService
from src.nlp.datetime_parser import DateTimeParser

logger = logging.getLogger(__name__)


class CalendarAgent:
    """AI Agent for natural calendar interactions"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.calendar_service = CalendarService()
        self.datetime_parser = DateTimeParser()
        self.model = "gpt-4o-mini"  # Cost-effective model
        
        # Define available functions
        self.functions = [
            {
                "name": "search_events",
                "description": "カレンダーから予定を検索します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "検索する日付 (YYYY-MM-DD形式)"
                        },
                        "keyword": {
                            "type": "string",
                            "description": "検索キーワード（オプション）"
                        }
                    },
                    "required": ["date"]
                }
            },
            {
                "name": "add_event",
                "description": "カレンダーに新しい予定を追加します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "予定のタイトル"
                        },
                        "datetime": {
                            "type": "string",
                            "description": "予定の日時 (ISO形式)"
                        },
                        "duration_minutes": {
                            "type": "integer",
                            "description": "予定の長さ（分）",
                            "default": 60
                        },
                        "location": {
                            "type": "string",
                            "description": "場所（オプション）"
                        }
                    },
                    "required": ["title", "datetime"]
                }
            },
            {
                "name": "delete_event",
                "description": "予定を削除します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "event_id": {
                            "type": "string",
                            "description": "削除する予定のID"
                        },
                        "title": {
                            "type": "string",
                            "description": "削除する予定のタイトル（IDが不明な場合）"
                        },
                        "date": {
                            "type": "string",
                            "description": "予定の日付（タイトルで検索する場合）"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "update_reminder_settings",
                "description": "リマインダーの設定を更新します",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reminder_enabled": {
                            "type": "boolean",
                            "description": "リマインダーを有効にするか"
                        },
                        "morning_time": {
                            "type": "string",
                            "description": "朝のリマインダー時刻 (HH:MM形式)"
                        },
                        "evening_time": {
                            "type": "string",
                            "description": "夜のリマインダー時刻 (HH:MM形式)"
                        },
                        "days_ahead": {
                            "type": "integer",
                            "description": "何日先までの予定を通知するか"
                        }
                    },
                    "required": []
                }
            },
            {
                "name": "check_subscription",
                "description": "現在の課金プランとAI利用状況を確認します",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            },
            {
                "name": "upgrade_subscription",
                "description": "課金プランをアップグレードします",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "plan": {
                            "type": "string",
                            "enum": ["basic", "premium"],
                            "description": "アップグレード先のプラン"
                        }
                    },
                    "required": ["plan"]
                }
            }
        ]
        
        self.system_prompt = """あなたは優秀なカレンダー管理アシスタントです。
ユーザーの自然な日本語を理解し、適切にカレンダーを操作します。

重要なルール：
1. 日時の解釈は日本時間(JST)で行う
2. 「明日」「来週」などの相対的な表現は正確に解釈する
3. 不明な点は確認を求める
4. 操作結果を分かりやすく説明する
5. 「さっきの」「その」などの指示代名詞は文脈から理解する

会話の例：
- 「明日の午後3時に会議」→ 明日の15:00に会議を追加
- 「来週の予定は？」→ 来週1週間の予定を検索
- 「さっきの会議キャンセル」→ 直前に話題になった会議を削除
"""
    
    async def process_message(
        self,
        user_id: str,
        message: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> tuple[str, List[Any]]:
        """
        Process user message with AI
        
        Args:
            user_id: LINE user ID
            message: User's message
            conversation_history: Past conversation context
            
        Returns:
            Tuple of (response text, function results)
        """
        try:
            # Build messages
            messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add conversation history
            if conversation_history:
                for entry in conversation_history[-5:]:  # Last 5 messages
                    messages.append({
                        "role": entry["role"],
                        "content": entry["content"]
                    })
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=self.functions,
                function_call="auto",
                temperature=0.7
            )
            
            assistant_message = response.choices[0].message
            
            # Process function calls
            function_results = []
            if assistant_message.function_call:
                function_name = assistant_message.function_call.name
                function_args = json.loads(assistant_message.function_call.arguments)
                
                logger.info(f"AI calling function: {function_name} with args: {function_args}")
                
                # Execute function
                result = await self._execute_function(
                    user_id,
                    function_name,
                    function_args
                )
                function_results.append(result)
                
                # Get final response with function result
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": assistant_message.function_call.arguments
                    }
                })
                messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(result, ensure_ascii=False)
                })
                
                # Get final response
                final_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.7
                )
                
                return final_response.choices[0].message.content, function_results
            
            return assistant_message.content, function_results
            
        except Exception as e:
            logger.error(f"AI Agent error: {e}")
            return "申し訳ございません。処理中にエラーが発生しました。", []
    
    async def _execute_function(
        self,
        user_id: str,
        function_name: str,
        args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute the specified function"""
        
        try:
            if function_name == "search_events":
                return await self._search_events(user_id, args)
            
            elif function_name == "add_event":
                return await self._add_event(user_id, args)
            
            elif function_name == "delete_event":
                return await self._delete_event(user_id, args)
            
            elif function_name == "update_reminder_settings":
                return await self._update_reminder_settings(user_id, args)
            
            elif function_name == "check_subscription":
                return await self._check_subscription(user_id, args)
            
            elif function_name == "upgrade_subscription":
                return await self._upgrade_subscription(user_id, args)
            
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            logger.error(f"Function execution error: {e}")
            return {"error": str(e)}
    
    async def _search_events(self, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search calendar events"""
        date_str = args.get("date")
        keyword = args.get("keyword")
        
        # Parse date
        try:
            date = datetime.fromisoformat(date_str).date()
        except:
            date = datetime.now().date()
        
        entities = {
            "date": date,
            "start_date": date,
            "end_date": date
        }
        
        events = await self.calendar_service.list_events(user_id, entities)
        
        # Filter by keyword if provided
        if keyword and events:
            events = [e for e in events if keyword.lower() in e.get("title", "").lower()]
        
        return {
            "date": date_str,
            "count": len(events),
            "events": events
        }
    
    async def _add_event(self, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Add calendar event"""
        title = args.get("title")
        datetime_str = args.get("datetime")
        duration = args.get("duration_minutes", 60)
        location = args.get("location")
        
        # Parse datetime
        try:
            start_time = datetime.fromisoformat(datetime_str)
        except:
            return {"error": "Invalid datetime format"}
        
        entities = {
            "title": title,
            "datetime": start_time,
            "duration_minutes": duration
        }
        
        if location:
            entities["location"] = location
        
        result = await self.calendar_service.add_event(user_id, entities)
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "event": {
                "title": title,
                "datetime": datetime_str,
                "duration": duration,
                "location": location
            }
        }
    
    async def _delete_event(self, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Delete calendar event"""
        event_id = args.get("event_id")
        title = args.get("title")
        date_str = args.get("date")
        
        # If event_id is provided, use it directly
        if event_id:
            # Direct deletion by ID (需要在calendar_service中实现)
            return {"message": "Event ID による削除は実装予定です"}
        
        # Search by title and date
        if title and date_str:
            try:
                date = datetime.fromisoformat(date_str).date()
            except:
                date = datetime.now().date()
            
            entities = {"date": date, "title": title}
            result = await self.calendar_service.delete_event(user_id, entities)
            
            return {
                "success": result.get("success", False),
                "message": result.get("message", "")
            }
        
        return {"error": "削除する予定を特定できませんでした"}
    
    async def _update_reminder_settings(self, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Update reminder settings"""
        from src.repositories.user_repository import UserRepository
        
        user_repo = UserRepository()
        
        # Build preferences update
        preferences = {}
        
        if "reminder_enabled" in args:
            preferences["reminder_enabled"] = args["reminder_enabled"]
        
        if "morning_time" in args:
            preferences["reminder_time_morning"] = args["morning_time"]
        
        if "evening_time" in args:
            preferences["reminder_time_evening"] = args["evening_time"]
        
        if "days_ahead" in args:
            preferences["reminder_days_ahead"] = args["days_ahead"]
        
        # Update preferences
        success = await user_repo.update_user_preferences(user_id, preferences)
        
        return {
            "success": success,
            "updated_settings": preferences,
            "message": "リマインダー設定を更新しました" if success else "設定の更新に失敗しました"
        }
    
    async def _check_subscription(self, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Check subscription status"""
        from src.services.subscription_service import SubscriptionService
        
        subscription_service = SubscriptionService()
        info = await subscription_service.get_subscription_info(user_id)
        
        if not info:
            return {"error": "プラン情報を取得できませんでした"}
        
        return {
            "plan": info['plan'],
            "plan_name": info['plan_name'],
            "price": info['price'],
            "ai_calls_used": info['ai_calls_used'],
            "ai_calls_limit": info['ai_calls_limit'],
            "ai_calls_remaining": info['ai_calls_remaining'],
            "features": info['features']
        }
    
    async def _upgrade_subscription(self, user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade subscription plan"""
        from src.services.subscription_service import SubscriptionService
        
        new_plan = args.get("plan", "basic")
        subscription_service = SubscriptionService()
        
        result = await subscription_service.upgrade_plan(user_id, new_plan)
        
        return {
            "success": result.get("success", False),
            "message": result.get("message", ""),
            "old_plan": result.get("old_plan"),
            "new_plan": result.get("new_plan")
        }