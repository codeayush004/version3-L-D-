from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.core.database import settings_collection, subjects_collection, batches_collection
from app.api.dependencies import verify_manager_role

router = APIRouter(prefix="/api/settings", tags=["settings"])

class ThresholdSettings(BaseModel):
    manager_id: str
    batch_id: str
    passing_score: float = 60.0
    recommended_score: float = 75.0
    borderline_score: float = 65.0

    weightages: dict = {}

@router.get("/")
async def get_settings(batch_id: str, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "adminviewer" in roles or "admin" in roles
    m_id = token_payload['identified_username']

    try:
        if not is_admin:
            batch = batches_collection.find_one({'batch_id': batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to access settings for this batch")

        settings = settings_collection.find_one({"batch_id": batch_id}, {"_id": 0})
        if not settings:
            # Dynamically calculate equal weight distributions based on the batch's subjects
            subjects_doc = subjects_collection.find_one({"batch_id": batch_id})
            subj_list = subjects_doc.get('list', []) if subjects_doc else []
            default_weights = {}
            if subj_list:
                weight_per_subj = round(100.0 / len(subj_list), 2)
                for s in subj_list:
                    name = s['name'] if isinstance(s, dict) else s
                    default_weights[name] = weight_per_subj

            return {
                "manager_id": m_id,
                "batch_id": batch_id,
                "passing_score": 60.0,
                "recommended_score": 75.0,
                "borderline_score": 65.0,
                "weightages": default_weights
            }
        return settings
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def update_settings(settings: ThresholdSettings, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "admin" in roles
    m_id = token_payload['identified_username']
    
    if "adminviewer" in roles and not is_admin and "ldmanager" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot modify settings")
        
    try:
        if not is_admin:
            batch = batches_collection.find_one({'batch_id': settings.batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to modify settings for this batch")

        settings_collection.update_one(
            {"batch_id": settings.batch_id},
            {"$set": settings.dict()},
            upsert=True
        )
        return {"message": "Settings updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
