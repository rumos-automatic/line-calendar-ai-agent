"""
Vercel entry point for main app
"""
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({
        "service": "LINE Google Calendar Agent",
        "version": "1.0.0",
        "environment": "vercel",
        "status": "healthy"
    })

# For Vercel
from mangum import Mangum
handler = Mangum(app)