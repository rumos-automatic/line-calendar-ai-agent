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
def handler(request, response):
    from mangum import Mangum
    asgi_handler = Mangum(app)
    return asgi_handler(request, response)