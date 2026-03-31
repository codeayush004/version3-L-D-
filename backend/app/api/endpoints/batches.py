from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from app.schemas.all_models import BatchModel
from app.core.database import (
    batches_collection, interns_collection, scores_collection, subjects_collection,
    feedback_collection, settings_collection
)

from app.api.dependencies import verify_manager_role
router = APIRouter(prefix="/api/batches", tags=["batches"])

@router.post("", status_code=201)
async def create_batch(data: BatchModel, token_payload: dict = Depends(verify_manager_role)):
    m_id = token_payload['identified_username']
    batch_id = str(ObjectId())
    
    # Check if admin/ldmanager (adminviewer shouldn't create batches realistically, but allowed_roles restricts global access)
    roles = [r.lower() for r in token_payload.get("roles", [])]
    if "adminviewer" in roles and "ldmanager" not in roles and "admin" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot create batches")

    batches_collection.insert_one({
        'batch_id': batch_id,
        'manager_id': m_id,
        'name': data.name,
        'department': data.department
    })
    
    # Initialize Subjects and Settings based on Department
    if data.department == "Data Engineering":
        de_subjects = [
            {"name": "Capstone project", "total_marks": 100},
            {"name": "Internal Project", "total_marks": 100},
            {"name": "Internal Assessment Scores", "total_marks": 100},
            {"name": "External Vendor Scores", "total_marks": 100},
            {"name": "Mentor Feedback", "total_marks": 100},
            {"name": "Viva Scores", "total_marks": 100},
            {"name": "Presentation/Communication", "total_marks": 100},
            {"name": "L&D Feedback", "total_marks": 100}
        ]
        subjects_collection.insert_one({
            'manager_id': m_id,
            'batch_id': batch_id,
            'list': de_subjects
        })
        
        # Default Weights for DE
        settings_collection.insert_one({
            'manager_id': m_id,
            'batch_id': batch_id,
            'passing_score': 60.0,
            'recommended_score': 75.0,
            'borderline_score': 65.0,
            'weightages': {
                "Capstone project": 20,
                "Internal Project": 15,
                "Internal Assessment Scores": 15,
                "External Vendor Scores": 10,
                "Mentor Feedback": 10,
                "Viva Scores": 10,
                "Presentation/Communication": 10,
                "L&D Feedback": 10
            }
        })
    else:
        # Data Ops Defaults
        ops_subjects = [
            {"name": "Assessment", "total_marks": 100},
            {"name": "Assignment", "total_marks": 100},
            {"name": "Tech Viva", "total_marks": 100},
            {"name": "Tech Demo", "total_marks": 100}
        ]
        subjects_collection.insert_one({
            'manager_id': m_id,
            'batch_id': batch_id,
            'list': ops_subjects
        })
        
        settings_collection.insert_one({
            'manager_id': m_id,
            'batch_id': batch_id,
            'passing_score': 60.0,
            'recommended_score': 75.0,
            'borderline_score': 65.0,
            'weightages': {
                "Assessment": 25,
                "Assignment": 25,
                "Tech Viva": 25,
                "Tech Demo": 25
            }
        })
    return {"message": "Batch created", "batch_id": batch_id, "name": data.name}

@router.get("")
async def get_batches(department: str = "Data Ops", token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "adminviewer" in roles or "admin" in roles
    m_id = token_payload['identified_username']

    query = {}
    if department:
        if department.lower() == "data ops":
            query['$or'] = [{'department': 'Data Ops'}, {'department': {'$exists': False}}]
        else:
            query['department'] = department
            
    if not is_admin:
        query['manager_id'] = {'$regex': f"^{m_id}$", '$options': 'i'}
    
    batches = list(batches_collection.find(query, {'_id': 0}))
    return batches

@router.delete("/{batch_id}")
async def delete_batch(batch_id: str, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "admin" in roles
    m_id = token_payload['identified_username']
    
    if "adminviewer" in roles and not is_admin and "ldmanager" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot delete batches")

    if is_admin:
        query = {'batch_id': batch_id}
    else:
        query = {'batch_id': batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}}
        
    res = batches_collection.delete_one(query)
    if res.deleted_count == 0:
        raise HTTPException(status_code=403, detail="Not authorized to delete this batch or batch not found")
        
    interns_collection.delete_many({'batch_id': batch_id})
    scores_collection.delete_many({'batch_id': batch_id})
    subjects_collection.delete_many({'batch_id': batch_id})
    feedback_collection.delete_many({'batch_id': batch_id})
    settings_collection.delete_many({'batch_id': batch_id})
    return {"message": "Batch deleted successfully"}
