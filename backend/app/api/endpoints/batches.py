from fastapi import APIRouter
from bson import ObjectId
from app.schemas.all_models import BatchModel
from app.core.database import (
    batches_collection, interns_collection, scores_collection, subjects_collection,
    feedback_collection, settings_collection, manager_sheets_collection, attempts_collection
)

router = APIRouter(prefix="/api/batches", tags=["batches"])

@router.post("", status_code=201)
async def create_batch(data: BatchModel):
    batch_id = str(ObjectId())
    batches_collection.insert_one({
        'batch_id': batch_id,
        'manager_id': data.manager_id,
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
            'manager_id': data.manager_id,
            'batch_id': batch_id,
            'list': de_subjects
        })
        
        # Default Weights for DE (Distributed across 8 subjects)
        settings_collection.insert_one({
            'manager_id': data.manager_id,
            'batch_id': batch_id,
            'passing_score': 60.0,
            'recommended_score': 85.0,
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
            'manager_id': data.manager_id,
            'batch_id': batch_id,
            'list': ops_subjects
        })
        
        settings_collection.insert_one({
            'manager_id': data.manager_id,
            'batch_id': batch_id,
            'passing_score': 60.0,
            'recommended_score': 85.0,
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
async def get_batches(manager_id: str, department: str = None):
    query = {'manager_id': manager_id}
    if department:
        query['department'] = department
        
    batches = list(batches_collection.find(query, {'_id': 0}))
    return batches

@router.delete("/{batch_id}")
async def delete_batch(batch_id: str, manager_id: str):
    batches_collection.delete_one({'batch_id': batch_id, 'manager_id': manager_id})
    interns_collection.delete_many({'batch_id': batch_id, 'manager_id': manager_id})
    scores_collection.delete_many({'batch_id': batch_id, 'manager_id': manager_id})
    subjects_collection.delete_many({'batch_id': batch_id, 'manager_id': manager_id})
    feedback_collection.delete_many({'batch_id': batch_id, 'manager_id': manager_id})
    settings_collection.delete_many({'batch_id': batch_id, 'manager_id': manager_id})
    manager_sheets_collection.delete_many({'batch_id': batch_id, 'manager_id': manager_id})
    attempts_collection.delete_many({'batch_id': batch_id, 'manager_id': manager_id})
    return {"message": "Batch deleted successfully"}
