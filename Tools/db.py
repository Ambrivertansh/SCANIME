"""
format:
_id: Vars.DB_NAME
user_id: {
     setting: {
        "file_name": "",
        "caption": "",
        ................
        .................
     }
}
.................
.................
.................
.................
"""

from .logger import get_logger
from pymongo import MongoClient
from bot import Vars
from asyncio import Lock

logger = get_logger(__name__)

client = MongoClient(Vars.DB_URL)
db = client[Vars.DB_NAME]

users = db["users"]
#acollection = db['premium']

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
            logger.info(f"Added new user: {user_id}")

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
