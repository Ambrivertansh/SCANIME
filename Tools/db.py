from .logger import get_logger
from pymongo import MongoClient
from bot import Vars
from asyncio import Lock
from datetime import datetime

logger = get_logger(__name__)

client = MongoClient(Vars.DB_URL)
db = client[Vars.DB_NAME]

users = db["users"]
messages = db["messages"]  # Core tracking for 6-Hour Auto-Delete

uts = users.find_one({"_id": Vars.DB_NAME})

if not uts:
    uts = {'_id': Vars.DB_NAME}
    users.insert_one(uts)

async def sync():
    """Sync the in-memory uts dictionary with database"""
    async with Lock():
        users.replace_one({'_id': Vars.DB_NAME}, uts)

async def add_user(user_id):
    """Add a new user with default settings"""
    async with Lock():
        user_id = str(user_id)
        if user_id not in uts:
            uts[user_id] = {"setting": {}}
            await sync()

async def get_user(user_id):
    """Get user data"""
    user_id = str(user_id)
    return uts.get(user_id)

async def update_setting(user_id, key, value):
    """Update a specific setting for a user"""
    async with Lock():
        user_id = str(user_id)
        if user_id not in uts:
            await add_user(user_id)
        if "setting" not in uts[user_id]:
            uts[user_id]["setting"] = {}
        
        uts[user_id]["setting"][key] = value
        await sync()

async def delete_user(user_id):
    """Remove a user from database"""
    user_id = str(user_id)
    if user_id in uts:
        del uts[user_id]
        await sync()

async def get_all_users():
    """Get all user IDs"""
    return [user_id for user_id in uts.keys() if user_id != "_id"]

async def user_exists(user_id):
    """Check if user exists"""
    user_id = str(user_id)
    return user_id in uts and user_id != "_id"

async def ensure_user(user_id):
    """Ensure user exists, create if not"""
    user_id = str(user_id)
    if not await user_exists(user_id):
        await add_user(user_id)

# ==========================================
# 6-HOUR AUTO-DELETE ENGINE PROTOCOL
# ==========================================
async def track_message(chat_id, message_id):
    """Track a message in MongoDB for the Auto-Delete Engine."""
    try:
        messages.insert_one({
            "chat_id": chat_id,
            "message_id": message_id,
            "createdAt": datetime.utcnow()
        })
        logger.info(f"Message {message_id} tracked for 6-hour deletion.")
    except Exception as e:
        logger.error(f"Failed to track message: {e}")
