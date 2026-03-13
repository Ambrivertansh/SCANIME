from typing import Dict, List, Any, Optional, Tuple
import asyncio
import string
import random
import  pyrogram.errors
from Tools.logger import get_logger

logger = get_logger(__name__)

def retry_on_flood(func):
    async def wrapper(*args, **kwargs):
        while True:
            try: 
                return await func(*args, **kwargs)
            except pyrogram.errors.FloodWait as e:
                logger.warning(f'FloodWait: waiting {e.value}s')
                await asyncio.sleep(int(e.value) + 3)
            except (pyrogram.errors.QueryIdInvalid, pyrogram.errors.MessageNotModified):
                raise
            except (pyrogram.errors.WebpageCurlFailed, pyrogram.errors.WebpageMediaEmpty):
                raise
            except Exception as e:
                if "struct.error: required argument is not a float" in str(e):
                    raise
                
                logger.exception(e) 
                raise
                
    return wrapper


class TaskCard:
    __slots__ = ('task_id', 'data', 'priority', 'user_id')
    def __init__(self, task_id: str, data: Any, user_id: int, priority: int = 1):
        self.task_id: str = task_id
        self.data = data
        self.user_id = user_id
        self.priority = priority

class AQueue:
    __slots__ = (
        'storage_data', 'data_users', 'ongoing_tasks',
        'maxsize', 'user_limit'
    )

    def __init__(self, maxsize: Optional[int] = None):
        self.storage_data: Dict[str, TaskCard] = {}  # {task_id: {TaskCard}}
        #self.data_users: Dict[int, List[str]] = {}  # {user_id: [task_ids]}
        self.ongoing_tasks: Dict[str, TaskCard] = {}
        self.maxsize = maxsize
        self.user_limit: int = 20

    async def get_random_id(self) -> str:
        """Generate unique 5-char task ID"""
        chars = string.ascii_letters + string.digits + string.punctuation
        while True:
            task_id = ''.join(random.choices(chars, k=4))
            if task_id not in self.storage_data and task_id not in self.ongoing_tasks:
                return task_id

    async def put(
        self, data: Any, user_id: int,
        priority: int = 1
    ) -> Tuple[str, int]:

        """Add task to queue"""
        if self.maxsize and len(self.storage_data) >= self.maxsize:
            raise asyncio.QueueFull("Queue full")

        task_id = await self.get_random_id()
        task_card = TaskCard(task_id, data, user_id, priority)
        self.storage_data[task_id] = task_card

        return task_id, len(self.storage_data)
    
    def get_available_tasks(self, user_id=None):
        """Return available tasks with better error handling"""
        tasks = [
            task_card
            for task_card in list(self.storage_data.values())
            if not user_id or task_card.user_id == user_id
        ]
        if not user_id:
            tasks = [
                task_card
                for task_card in tasks
                if self.get_ongoing_count(task_card.user_id) == 0
            ]
            
        sorted_tasks = sorted(tasks, key=lambda x: (x.priority != 0, tasks.index(x)))
        if not sorted_tasks:
            return None

        return sorted_tasks if user_id else sorted_tasks[0]
    
    async def get(self) -> Tuple[Any, int, str]:
        """Get next available task"""
        while True:
            if not self.storage_data:
                await asyncio.sleep(0.1)
                continue

            # Find available tasks (users with no ongoing tasks)
            available_tasks = self.get_available_tasks()
            
            if not available_tasks or isinstance(available_tasks, list):
                await asyncio.sleep(0.1)
                continue


            # Move to ongoing
            self.ongoing_tasks[available_tasks.task_id] = available_tasks
            self.storage_data.pop(available_tasks.task_id)

            return available_tasks.data, available_tasks.user_id, available_tasks.task_id

    async def delete_task(self, task_id: str) -> bool:
        """Delete specific task"""
        if task_id in self.storage_data:
            self.storage_data.pop(task_id)
            return True
        return False

    async def delete_tasks(self, user_id: int) -> int:
        """Delete all tasks for user"""
        user_tasks = self.get_available_tasks(user_id=user_id)
        
        if not user_tasks or not isinstance(user_tasks, list):
            return 0
        
        deleted = 0
        for task_card in user_tasks:
            self.storage_data.pop(task_card.task_id)
            try:
                try:
                    await retry_on_flood(task_card.data.sts.delete)()
                except Exception:
                    pass
            except Exception:
                pass
            deleted += 1

        return deleted

    def get_count(self, user_id: int) -> int:
        """Get user's pending task count"""
        users_tasks = self.get_available_tasks(user_id=user_id)
        users_tasks = users_tasks if isinstance(users_tasks, list) else [users_tasks] if users_tasks else []

        return int(len(users_tasks)) if users_tasks else 0
    
    def get_ongoing_count(self, user_id: int) -> int:
        """Get user's ongoing task count"""
        return sum(1 for t in list(self.ongoing_tasks.values()) if str(t.user_id) == str(user_id))
    
    def task_exists(self, task_id: str) -> bool:
        """Check if task exists"""
        return task_id in self.storage_data

    def qsize(self) -> int:
        return len(self.storage_data)

    def empty(self) -> bool:
        return not self.storage_data

    def is_user_hit_limit(self, user_id) -> bool:
        return self.get_count(user_id) >= self.user_limit

    async def task_done(self, task_id: str) -> bool:
        """Mark task as done"""
        if task_id in self.ongoing_tasks:
            del self.ongoing_tasks[task_id]
            return True
        return False



Queue = AQueue()
