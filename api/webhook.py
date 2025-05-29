"""
Vercel webhook endpoint
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from linebot.v3.webhook import WebhookParser
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
import logging

from src.core.config import settings
from src.core.logging import setup_logging
from src.services.message_handler import handle_text_message

# Setup logging for Vercel
setup_logging()
logger = logging.getLogger(__name__)

# Initialize webhook parser
try:
    parser = WebhookParser(settings.LINE_CHANNEL_SECRET)
except Exception as e:
    logger.error(f"Failed to initialize webhook parser: {e}")
    parser = None

# Create FastAPI app for this endpoint
app = FastAPI()

@app.post("/")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle LINE webhook events"""
    
    if not parser:
        logger.error("Webhook parser not initialized")
        raise HTTPException(status_code=500, detail="Service unavailable")
    
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
    return JSONResponse({"status": "ok"})

# Vercel handler
from mangum import Mangum
handler = Mangum(app)