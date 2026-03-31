from fastapi import APIRouter, HTTPException, Depends
from app.schemas.all_models import SubjectDeleteModel, SubjectUpdateModel
from app.core.database import subjects_collection, scores_collection, batches_collection
from app.api.dependencies import verify_manager_role

router = APIRouter(prefix="/api/subjects", tags=["subjects"])

@router.get("")
async def get_subjects(batch_id: str, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "adminviewer" in roles or "admin" in roles
    m_id = token_payload['identified_username']
    
    try:
        if not is_admin:
            batch = batches_collection.find_one({'batch_id': batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to access subjects for this batch")

        doc = subjects_collection.find_one({'batch_id': batch_id})
        if not doc: return []
        
        raw_list = doc.get('list') or doc.get('subjects') or []
        standardized = []
        for item in raw_list:
            if isinstance(item, dict):
                standardized.append(item)
            else:
                standardized.append({"name": str(item), "total_marks": 100})
        return standardized
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("")
async def delete_subject(data: SubjectDeleteModel, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "admin" in roles
    m_id = token_payload['identified_username']

    if "adminviewer" in roles and not is_admin and "ldmanager" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot modify subjects")
        
    try:
        if not is_admin:
            batch = batches_collection.find_one({'batch_id': data.batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to modify subjects for this batch")

        # Pull matching object or raw string
        subjects_collection.update_one(
            {'batch_id': data.batch_id},
            {'$pull': {'list': {'name': data.subject}}}
        )
        subjects_collection.update_one(
            {'batch_id': data.batch_id},
            {'$pull': {'list': data.subject}}
        )
        # Clean up scores
        scores_collection.update_many(
            {'batch_id': data.batch_id},
            {'$unset': {f'scores.{data.subject}': ""}}
        )
        return {"message": f"Subject {data.subject} deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("")
async def update_subject(data: SubjectUpdateModel, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "admin" in roles
    m_id = token_payload['identified_username']

    if "adminviewer" in roles and not is_admin and "ldmanager" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot modify subjects")
        
    try:
        if not is_admin:
            batch = batches_collection.find_one({'batch_id': data.batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to modify subjects for this batch")

        subjects_doc = subjects_collection.find_one({'batch_id': data.batch_id})
        if subjects_doc:
            new_list = []
            found = False
            raw_list = subjects_doc.get('list') or subjects_doc.get('subjects') or []
            for item in raw_list:
                item_name = item['name'] if isinstance(item, dict) else item
                if item_name == data.old_name:
                    found = True
                    new_item = {
                        'name': data.new_name if data.new_name else data.old_name,
                        'total_marks': int(data.total_marks) if data.total_marks is not None else (item.get('total_marks', 100) if isinstance(item, dict) else 100)
                    }
                    new_list.append(new_item)
                else:
                    new_list.append(item if isinstance(item, dict) else {"name": item, "total_marks": 100})
            
            if found:
                subjects_collection.update_one(
                    {'_id': subjects_doc['_id']},
                    {'$set': {'list': new_list}, '$unset': {'subjects': ""}}
                )
                if data.new_name and data.new_name != data.old_name:
                    scores_collection.update_many(
                        {'batch_id': data.batch_id},
                        {'$rename': {f'scores.{data.old_name}': f'scores.{data.new_name}'}}
                    )
        return {"message": "Subject updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
