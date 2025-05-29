"""
Vercel entry point
"""
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.main import app

# Vercel expects handler function
def handler(request, response):
    return app(request, response)