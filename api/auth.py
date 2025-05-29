"""
Vercel authentication callbacks
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import RedirectResponse
import logging

from src.services.auth_service import exchange_code_for_tokens, save_user_tokens
from src.repositories.user_repository import UserRepository

app = FastAPI()
logger = logging.getLogger(__name__)

@app.get("/google/callback")
async def google_auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None)
):
    """Handle Google OAuth callback"""
    
    if error:
        logger.error(f"Google OAuth error: {error}")
        return RedirectResponse(url=f"https://line.me/R/oauthCallback?error={error}")
    
    try:
        # Get auth state
        user_repo = UserRepository()
        auth_state = await user_repo.get_auth_state(state)
        
        if not auth_state:
            raise HTTPException(status_code=400, detail="Invalid state")
        
        line_user_id = auth_state['line_user_id']
        code_verifier = auth_state['code_verifier']
        
        # Exchange code for tokens
        tokens = await exchange_code_for_tokens(code, code_verifier)
        
        # Save tokens
        success = await save_user_tokens(line_user_id, tokens)
        
        if success:
            # Redirect back to LIFF
            return RedirectResponse(url="https://line.me/R/oauthCallback?code=success")
        else:
            return RedirectResponse(url="https://line.me/R/oauthCallback?error=save_failed")
            
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        return RedirectResponse(url=f"https://line.me/R/oauthCallback?error=callback_failed")

# Vercel handler
def handler(request, response):
    from mangum import Mangum
    asgi_handler = Mangum(app)
    return asgi_handler(request, response)