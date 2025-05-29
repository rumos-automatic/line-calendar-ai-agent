"""
Vercel health check endpoint
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def health_check():
    """Basic health check endpoint for Vercel"""
    return JSONResponse({"status": "healthy", "runtime": "vercel"})

# Vercel handler
from mangum import Mangum
handler = Mangum(app)