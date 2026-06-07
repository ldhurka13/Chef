"""
MongoDB database connection and initialization.
"""
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_URL, DB_NAME

# MongoDB connection
client = AsyncIOMotorClient(MONGO_URL)
db = client[DB_NAME]

async def close_db_connection():
    """Close MongoDB connection on shutdown."""
    client.close()
