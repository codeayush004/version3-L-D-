from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.database import settings_collection

router = APIRouter(prefix="/api/settings", tags=["settings"])

class ThresholdSettings(BaseModel):
    manager_id: str
    batch_id: str
    passing_score: float = 60.0
    recommended_score: float = 85.0
    borderline_score: float = 65.0
    weightages: dict = {
        "Assessment": 25,
        "Assignment": 25,
        "Tech Viva": 25,
        "Tech Demo": 25
    }

@router.get("/")
async def get_settings(manager_id: str, batch_id: str):
    try:
        settings = settings_collection.find_one({"manager_id": manager_id, "batch_id": batch_id}, {"_id": 0})
        if not settings:
            # Return defaults if not set
            return {
                "manager_id": manager_id,
                "batch_id": batch_id,
                "passing_score": 60.0,
                "recommended_score": 85.0,
                "borderline_score": 65.0,
                "weightages": {
                    "Assessment": 25,
                    "Assignment": 25,
                    "Tech Viva": 25,
                    "Tech Demo": 25
                }
            }
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def update_settings(settings: ThresholdSettings):
    try:
        settings_collection.update_one(
            {"manager_id": settings.manager_id, "batch_id": settings.batch_id},
            {"$set": settings.dict()},
            upsert=True
        )
        return {"message": "Settings updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
