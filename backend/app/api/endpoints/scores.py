from fastapi import APIRouter, HTTPException, Depends
from app.schemas.all_models import ScoreUpdateModel, BulkScoreUpdateModel
from app.core.database import interns_collection, scores_collection, subjects_collection, feedback_collection
from app.api.dependencies import verify_azure_token, verify_manager_role

router = APIRouter(prefix="/api", tags=["scores"])

@router.get("/scores")
async def get_scores(manager_id: str, batch_id: str, token_payload: dict = Depends(verify_azure_token)):
    try:
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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update-score")
async def update_score(data: ScoreUpdateModel, token_payload: dict = Depends(verify_manager_role)):
    try:
        # 1. Update the actual score
        scores_collection.update_one(
            {'EmpID': data.EmpID, 'manager_id': data.manager_id, 'batch_id': data.batch_id},
            {'$set': {f'scores.{data.subject}': data.score}},
            upsert=True
        )
        
        # 2. Sync subjects list
        if data.total_marks is not None:
            subj_doc = subjects_collection.find_one({'manager_id': data.manager_id, 'batch_id': data.batch_id})
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
                {'manager_id': data.manager_id, 'batch_id': data.batch_id},
                {'$set': {'list': new_list}, '$unset': {'subjects': ""}},
                upsert=True
            )
        
        return {"message": "Score updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/bulk-update")
async def bulk_update_scores(data: BulkScoreUpdateModel, token_payload: dict = Depends(verify_manager_role)):
    try:
        from pymongo import UpdateOne
        operations = []
        for update in data.updates:
            emp_id = update.get("EmpID")
            subject = update.get("subject")
            score = update.get("score")
            
            if emp_id and subject and score is not None:
                operations.append(
                    UpdateOne(
                        {'EmpID': emp_id, 'manager_id': data.manager_id, 'batch_id': data.batch_id},
                        {'$set': {f'scores.{subject}': float(score)}},
                        upsert=True
                    )
                )
        
        if operations:
            scores_collection.bulk_write(operations)
            
        return {"message": "Scores updated successfully", "count": len(operations)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
