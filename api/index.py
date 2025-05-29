"""
Simple Vercel API endpoint for testing
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from mangum import Mangum

app = FastAPI()

@app.get("/")
async def root():
    """Simple test endpoint"""
    return JSONResponse({
        "message": "🤖 LINE Google Calendar AI Agent",
        "status": "healthy",
        "environment": "vercel"
    })

@app.get("/test")
async def test():
    """Test endpoint"""
    return JSONResponse({
        "test": "success",
        "timestamp": "2025-01-29"
    })

# Vercel handler
handler = Mangum(app)