import motor.motor_asyncio
from config import Config
from bson import ObjectId
from typing import Dict, Any, Optional

class Database:
    def __init__(self):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGODB_URI)
        self.db = self.client[Config.DATABASE_NAME]
        self.users = self.db.users
        self.jobs = self.db.jobs
        self.settings = self.db.settings
    
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        return await self.users.find_one({"user_id": user_id})
    
    async def create_user(self, user_id: int, username: str = "") -> Dict[str, Any]:
        user_data = {
            "user_id": user_id,
            "username": username,
            "join_date": datetime.now(),
            "premium": False,
            "banned": False,
            "usage_stats": {
                "videos_processed": 0,
                "audios_processed": 0,
                "documents_processed": 0,
                "urls_processed": 0
            }
        }
        await self.users.insert_one(user_data)
        return user_data
    
    async def update_user_stats(self, user_id: int, stat_type: str):
        await self.users.update_one(
            {"user_id": user_id},
            {"$inc": {f"usage_stats.{stat_type}": 1}}
        )
    
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        settings = await self.settings.find_one({"user_id": user_id})
        if not settings:
            # Default settings
            default_settings = {
                "user_id": user_id,
                "rename_pattern": "{filename}",
                "upload_mode": "video",  # video/document
                "file_quality": "high",  # high/medium/low
                "thumbnail": None,
                "audio_merge_mode": "replace",  # replace/merge
                "auto_trim_audio": False,
                "audio_compression": "normal"
            }
            await self.settings.insert_one(default_settings)
            return default_settings
        return settings
    
    async def update_user_settings(self, user_id: int, updates: Dict[str, Any]):
        await self.settings.update_one(
            {"user_id": user_id},
            {"$set": updates},
            upsert=True
        )
    
    async def create_job(self, user_id: int, job_type: str, file_id: str = "") -> str:
        job_data = {
            "user_id": user_id,
            "job_type": job_type,
            "file_id": file_id,
            "status": "queued",
            "created_at": datetime.now(),
            "progress": 0
        }
        result = await self.jobs.insert_one(job_data)
        return str(result.inserted_id)
    
    async def update_job_progress(self, job_id: str, progress: int):
        await self.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"progress": progress, "status": "processing"}}
        )
    
    async def complete_job(self, job_id: str):
        await self.jobs.update_one(
            {"_id": ObjectId(job_id)},
            {"$set": {"progress": 100, "status": "completed"}}
        )
    
    async def get_user_jobs(self, user_id: int) -> list:
        return await self.jobs.find({"user_id": user_id}).sort("created_at", -1).to_list(10)

# Global database instance
db = Database()
