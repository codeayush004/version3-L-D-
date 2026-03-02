from fastapi import APIRouter, HTTPException
from datetime import datetime
from app.schemas.all_models import AttemptUpdateModel
from app.core.database import attempts_collection, interns_collection, subjects_collection

router = APIRouter(prefix="/api", tags=["attempts"])

@router.get("/attempts-grid")
async def get_attempts_grid(manager_id: str, batch_id: str):
    try:
        interns = list(interns_collection.find({'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0}))
        attempts = list(attempts_collection.find({'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0}))
        
        # Map attempts to intern/subject
        attempt_map = {}
        for a in attempts:
            eid = a['EmpID']
            sub = a['subject']
            if eid not in attempt_map: attempt_map[eid] = {}
            attempt_map[eid][sub] = a['attempt_note']
            
        combined = []
        for intern in interns:
            combined.append({**intern, 'attempts': attempt_map.get(intern['EmpID'], {})})
            
        return combined
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-attempt")
async def update_attempt(data: AttemptUpdateModel):
    try:
        attempts_collection.update_one(
            {'EmpID': data.EmpID, 'manager_id': data.manager_id, 'batch_id': data.batch_id, 'subject': data.subject},
            {'$set': {'attempt_note': data.attempt_note, 'updated_at': datetime.now().isoformat()}},
            upsert=True
        )
        return {"message": "Attempt updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
