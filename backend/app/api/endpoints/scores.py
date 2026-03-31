from fastapi import APIRouter, HTTPException, Depends
from app.schemas.all_models import ScoreUpdateModel, BulkScoreUpdateModel
from app.core.database import interns_collection, scores_collection, subjects_collection, feedback_collection, batches_collection
from app.api.dependencies import verify_azure_token, verify_manager_role

router = APIRouter(prefix="/api", tags=["scores"])

@router.get("/scores")
async def get_scores(batch_id: str, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "adminviewer" in roles or "admin" in roles
    m_id = token_payload['identified_username']
    
    try:
        if not is_admin:
            # Verify ownership
            batch = batches_collection.find_one({'batch_id': batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to access this batch")

        interns = list(interns_collection.find({'batch_id': batch_id}, {'_id': 0}))
        scores = list(scores_collection.find({'batch_id': batch_id}, {'_id': 0}))
        
        scores_map = {s['EmpID']: s.get('scores', {}) for s in scores}
        
        # Fetch feedback to get the latest comment for each intern
        feedbacks = list(feedback_collection.find({'batch_id': batch_id}, {'_id': 0}).sort('date', -1))
        feedback_map = {}
        for f in feedbacks:
            if f['EmpID'] not in feedback_map:
                feedback_map[f['EmpID']] = f.get('text', '')
        
        combined_data = []
        for intern in interns:
            emp_id = intern['EmpID']
            intern_scores = scores_map.get(emp_id, {})
            latest_feedback = feedback_map.get(emp_id, 'No feedback yet')
            combined_data.append({**intern, **intern_scores, 'latest_feedback': latest_feedback})
            
        return combined_data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-score")
async def update_score(data: ScoreUpdateModel, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "admin" in roles
    m_id = token_payload['identified_username']
    
    if "adminviewer" in roles and not is_admin and "ldmanager" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot modify scores")

    try:
        if not is_admin:
            batch = batches_collection.find_one({'batch_id': data.batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to modify this batch")

        # 1. Update the actual score
        scores_collection.update_one(
            {'EmpID': data.EmpID, 'batch_id': data.batch_id},
            {'$set': {f'scores.{data.subject}': data.score}},
            upsert=True
        )
        
        # 2. Sync subjects list
        if data.total_marks is not None:
            subj_doc = subjects_collection.find_one({'batch_id': data.batch_id})
            existing_list = []
            if subj_doc:
                existing_list = subj_doc.get('list') or subj_doc.get('subjects') or []
            
            new_list = []
            found = False
            for item in existing_list:
                iname = item['name'] if isinstance(item, dict) else item
                if iname == data.subject:
                    found = True
                    new_list.append({"name": data.subject, "total_marks": int(data.total_marks)})
                else:
                    new_list.append(item if isinstance(item, dict) else {"name": item, "total_marks": 100})
            
            if not found:
                new_list.append({"name": data.subject, "total_marks": int(data.total_marks)})
                
            subjects_collection.update_one(
                {'batch_id': data.batch_id},
                {'$set': {'list': new_list}, '$unset': {'subjects': ""}},
                upsert=True
            )
        
        return {"message": "Score updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bulk-update")
async def bulk_update_scores(data: BulkScoreUpdateModel, token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "admin" in roles
    m_id = token_payload['identified_username']
    
    if "adminviewer" in roles and not is_admin and "ldmanager" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot modify scores")

    try:
        if not is_admin:
            batch = batches_collection.find_one({'batch_id': data.batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
            if not batch:
                raise HTTPException(status_code=403, detail="Not authorized to modify this batch")

        from pymongo import UpdateOne
        operations = []
        for update in data.updates:
            emp_id = update.get("EmpID")
            subject = update.get("subject")
            score = update.get("score")
            
            if emp_id and subject and score is not None:
                operations.append(
                    UpdateOne(
                        {'EmpID': emp_id, 'batch_id': data.batch_id},
                        {'$set': {f'scores.{subject}': float(score)}},
                        upsert=True
                    )
                )
        
        if operations:
            scores_collection.bulk_write(operations)
            
        return {"message": "Scores updated successfully", "count": len(operations)}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
