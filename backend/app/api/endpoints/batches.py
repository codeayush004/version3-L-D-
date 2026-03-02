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
        'name': data.name
    })
    return {"message": "Batch created", "batch_id": batch_id, "name": data.name}

@router.get("")
async def get_batches(manager_id: str):
    batches = list(batches_collection.find({'manager_id': manager_id}, {'_id': 0}))
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
