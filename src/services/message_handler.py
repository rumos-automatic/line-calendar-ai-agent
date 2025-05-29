"""
Message handler service for processing LINE messages
"""
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import (
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
    Configuration
)
import logging

from src.core.config import settings
from src.repositories.user_repository import UserRepository
from src.services.nlp_service import NLPService
from src.services.calendar_service import CalendarService
from src.services.conversation_service import ConversationService
from src.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

# LINE Bot API configuration
configuration = Configuration(
    host="https://api.line.me",
    access_token=settings.LINE_CHANNEL_ACCESS_TOKEN
)


async def handle_text_message(event: MessageEvent):
    """
    Handle incoming text message from LINE
    
    Args:
        event: LINE message event
    """
    try:
        line_user_id = event.source.user_id
        message_text = event.message.text
        reply_token = event.reply_token
        
        logger.info(f"Processing message from {line_user_id}: {message_text}")
        
        # Check if user is linked
        user_repo = UserRepository()
        user = await user_repo.get_user(line_user_id)
        
        if not user or not user.get('google_email'):
            # User not linked
            reply_text = (
                "Googleカレンダーとの連携が必要です。\n"
                "以下のリンクから連携設定を行ってください：\n"
                f"{settings.BASE_URL}/liff?openExternalBrowser=1"
            )
            await send_reply(reply_token, reply_text)
            return
        
        # Check subscription and AI availability
        subscription_service = SubscriptionService()
        can_use_ai, reason = await subscription_service.check_ai_availability(line_user_id)
        
        # Global AI setting must also be enabled
        if can_use_ai and settings.USE_AI_AGENT and settings.OPENAI_API_KEY:
            # Use AI agent for natural conversation
            conversation_service = ConversationService()
            reply_text = await conversation_service.process_message_with_ai(
                line_user_id,
                message_text
            )
            
            # Increment usage counter
            await subscription_service.increment_ai_usage(line_user_id)
            
        elif not can_use_ai and reason:
            # User requested AI but can't use it
            user_prefs = user.get('preferences', {})
            if user_prefs.get('use_ai_agent', False):
                reply_text = f"{reason}\n\nパターン認識モードで処理します。"
                # Fall back to pattern matching
                reply_text += await _process_with_pattern_matching(
                    line_user_id, message_text
                )
            else:
                # Process with pattern matching
                reply_text = await _process_with_pattern_matching(
                    line_user_id, message_text
                )
        else:
            # Fall back to pattern matching
            reply_text = await _process_with_pattern_matching(
                line_user_id, message_text
            )
        
        await send_reply(reply_token, reply_text)
        
    except Exception as e:
        logger.error(f"Error handling message: {e}", exc_info=True)
        try:
            await send_reply(
                reply_token,
                "エラーが発生しました。しばらくしてからもう一度お試しください。"
            )
        except:
            pass


async def send_reply(reply_token: str, message: str):
    """
    Send reply message to LINE
    
    Args:
        reply_token: Reply token from LINE
        message: Message text to send
    """
    try:
        async with ApiClient(configuration=configuration) as api_client:
            api = MessagingApi(api_client)
            
            request = ReplyMessageRequest(
                reply_token=reply_token,
                messages=[TextMessage(text=message)]
            )
            
            await api.reply_message(request)
            
    except Exception as e:
        logger.error(f"Failed to send reply: {e}")


async def _process_with_pattern_matching(line_user_id: str, message_text: str) -> str:
    """
    Process message with pattern matching
    
    Args:
        line_user_id: LINE user ID
        message_text: Message text
        
    Returns:
        Reply text
    """
    try:
        nlp_service = NLPService()
        intent, entities = await nlp_service.process_message(message_text)
        
        logger.info(f"Pattern matching - Intent: {intent}, Entities: {entities}")
        
        # Handle based on intent
        calendar_service = CalendarService()
        
        if intent == "add_event":
            result = await calendar_service.add_event(line_user_id, entities)
            return result.get('message', '予定を追加しました。')
            
        elif intent == "list_events":
            events = await calendar_service.list_events(line_user_id, entities)
            return format_events_list(events)
            
        elif intent == "delete_event":
            result = await calendar_service.delete_event(line_user_id, entities)
            return result.get('message', '予定を削除しました。')
            
        elif intent == "update_event":
            result = await calendar_service.update_event(line_user_id, entities)
            return result.get('message', '予定を更新しました。')
            
        elif intent == "check_subscription":
            subscription_service = SubscriptionService()
            info = await subscription_service.get_subscription_info(line_user_id)
            if info:
                return (
                    f"📊 **現在のプラン情報**\n\n"
                    f"プラン: {info['plan_name']}\n"
                    f"料金: {info['price']}円/月\n"
                    f"AI利用回数: {info['ai_calls_used']}/{info['ai_calls_limit']}\n"
                    f"残り回数: {info['ai_calls_remaining']}\n\n"
                    f"{'✅' if info['features']['ai_agent'] else '❌'} AIエージェントモード\n"
                    f"✅ パターン認識モード"
                )
            return "プラン情報を取得できませんでした。"
            
        elif intent == "upgrade_plan":
            # Extract plan name from message
            if "プレミアム" in message_text:
                new_plan = "premium"
            elif "ベーシック" in message_text:
                new_plan = "basic"
            else:
                return (
                    "アップグレード可能なプラン：\n\n"
                    "🥉 **無料プラン** (0円/月)\n"
                    "- パターン認識モード\n"
                    "- AI利用: 月10回まで\n\n"
                    "🥈 **ベーシックプラン** (500円/月)\n"
                    "- AIエージェントモード\n"
                    "- AI利用: 月100回まで\n\n"
                    "🥇 **プレミアムプラン** (1,500円/月)\n"
                    "- AIエージェントモード\n"
                    "- AI利用: 無制限\n\n"
                    "「ベーシックプランに変更」または「プレミアムプランに変更」と入力してください。"
                )
            
            subscription_service = SubscriptionService()
            result = await subscription_service.upgrade_plan(line_user_id, new_plan)
            return result.get('message', 'プランの変更に失敗しました。')
            
        else:
            return (
                "申し訳ございません。理解できませんでした。\n"
                "以下のような形式でお試しください：\n"
                "・「明日の15時に会議」\n"
                "・「今日の予定は？」\n"
                "・「明日の予定を教えて」"
            )
            
    except Exception as e:
        logger.error(f"Error in pattern matching: {e}")
        return "エラーが発生しました。"


def format_events_list(events: list) -> str:
    """
    Format events list for display
    
    Args:
        events: List of calendar events
        
    Returns:
        Formatted text message
    """
    if not events:
        return "予定はありません。"
    
    lines = ["📅 予定一覧：\n"]
    
    for event in events:
        start_time = event.get('start_time', '')
        end_time = event.get('end_time', '')
        title = event.get('title', '(タイトルなし)')
        
        if start_time and end_time:
            lines.append(f"• {start_time} - {end_time}: {title}")
        elif start_time:
            lines.append(f"• {start_time}: {title}")
        else:
            lines.append(f"• {title}")
    
    return "\n".join(lines)