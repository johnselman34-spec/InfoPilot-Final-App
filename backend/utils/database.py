"""
Database connection and utilities
"""
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'infopilot_db')

# MongoDB client - shared across the application
client = None
db = None

async def init_database():
    """Initialize database connection with retry logic"""
    global client, db
    
    # Connection with robust settings
    client = AsyncIOMotorClient(
        MONGO_URL,
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000,
        maxPoolSize=50,
        retryWrites=True
    )
    
    db = client[DB_NAME]
    return db

async def close_database():
    """Close database connection"""
    global client
    if client:
        client.close()

def get_db():
    """Get database instance"""
    return db
