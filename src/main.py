"""
main.py — Application entry point.
Creates the FastAPI app, connects to MongoDB on startup,
and registers all route modules.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient

from helpers.config import get_settings
from routes.base import base_router
from routes.data import data_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan context manager.
    Handles startup (connect to MongoDB) and shutdown (close connection).
    """
    settings = get_settings()

    # Startup Phase
    # Connect to MongoDB via Motor (async driver)
    motor_client = AsyncIOMotorClient(settings.MONGODB_URI)
    app.mongodb = motor_client[settings.MONGODB_DB_NAME]

    print(f"Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    print(f"{settings.APP_NAME} v{settings.APP_VERSION} is ready")

    yield  # App runs here

    # Shutdown Phase
    motor_client.close()
    print("MongoDB connection closed")


# Create the FastAPI application
app = FastAPI(
    title=get_settings().APP_NAME,
    version=get_settings().APP_VERSION,
    lifespan=lifespan,
)

# Register Routers
app.include_router(base_router)
app.include_router(data_router)
