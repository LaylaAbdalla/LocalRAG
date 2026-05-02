"""
routes/base.py Health check welcome endpoint
Returns the app name and version to confirm the API is running
"""

from fastapi import APIRouter, Depends
from helpers.config import Settings, get_settings

# Create a router with the /api prefix
base_router = APIRouter(prefix="/api", tags=["Health"])


@base_router.get("/")
async def welcome(app_settings: Settings = Depends(get_settings)):
    """
    GET /api/
    Simple health-check endpoint.
    """
    return {
        "message": f"Welcome to {app_settings.APP_NAME} v{app_settings.APP_VERSION}!"
    }
