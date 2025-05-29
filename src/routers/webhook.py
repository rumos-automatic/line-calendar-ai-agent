"""
LINE Webhook handler
"""
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import logging

from src.core.config import settings
from src.services.message_handler import handle_text_message

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize webhook parser
parser = WebhookParser(settings.LINE_CHANNEL_SECRET)


@router.post("")
async def handle_webhook(
    request: Request,
    background_tasks: BackgroundTasks
):
    """Handle LINE webhook events"""
    
    # Get signature from header
    signature = request.headers.get("X-Line-Signature")
    if not signature:
        logger.warning("Webhook request without signature")
        raise HTTPException(status_code=400, detail="Missing signature")
    
    # Get request body
    body = await request.body()
    body_str = body.decode("utf-8")
    
    # Parse webhook events
    try:
        events = parser.parse(body_str, signature)
    except InvalidSignatureError:
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid signature")
    except Exception as e:
        logger.error(f"Failed to parse webhook: {e}")
        raise HTTPException(status_code=500, detail="Parse error")
    
    # Process events in background
    for event in events:
        if isinstance(event, MessageEvent) and isinstance(event.message, TextMessageContent):
            background_tasks.add_task(
                handle_text_message,
                event
            )
        else:
            logger.info(f"Unhandled event type: {type(event)}")
    
    # Return immediately to LINE
    return {"status": "ok"}