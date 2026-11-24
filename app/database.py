from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from typing import Optional

class Database:
    client: Optional[AsyncIOMotorClient] = None

db = Database()

def get_database():
    if db.client is None:
        db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    return db.client[settings.DB_NAME]

async def close_database():
    if db.client is not None:
        db.client.close()
        db.client = None
