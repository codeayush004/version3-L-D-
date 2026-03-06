from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.schemas.all_models import ManagerSheetLinkModel, SyncFeedbackModel
from app.core.database import manager_sheets_collection, feedback_collection
import os
import shutil
import pandas as pd
import requests
from io import StringIO
from datetime import datetime

router = APIRouter(prefix="/api", tags=["manager-sheet"])

UPLOAD_DIR = "uploads/manager_sheets"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

@router.get("/manager-sheet")
async def get_manager_sheet(manager_id: str, batch_id: str):
    try:
        res = manager_sheets_collection.find_one({'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0})
        return res if res else {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manager-sheet/link")
async def update_sheet_link(data: ManagerSheetLinkModel):
    try:
        manager_sheets_collection.update_one(
            {'manager_id': data.manager_id, 'batch_id': data.batch_id},
            {'$set': {
                'sheet_url': data.sheet_url,
                'type': 'link',
                'updated_at': datetime.now().isoformat()
            }},
            upsert=True
        )
        return {"message": "Sheet link updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manager-sheet/upload")
async def upload_sheet_file(
    manager_id: str = Form(...),
    batch_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        filename = f"{manager_id}_{batch_id}_{file.filename}"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        manager_sheets_collection.update_one(
            {'manager_id': manager_id, 'batch_id': batch_id},
            {'$set': {
                'file_path': filepath,
                'filename': file.filename,
                'type': 'upload',
                'updated_at': datetime.now().isoformat()
            }},
            upsert=True
        )
        return {"message": "File uploaded successfully", "filename": file.filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manager-sheet/sync-feedback")
async def sync_feedback(data: SyncFeedbackModel):
    try:
        sheet_doc = manager_sheets_collection.find_one({'manager_id': data.manager_id, 'batch_id': data.batch_id})
        if not sheet_doc or sheet_doc.get('type') != 'link':
            raise HTTPException(status_code=400, detail="No Google Sheet link found for this batch")
        
        url = sheet_doc.get('sheet_url')
        if not url or "docs.google.com" not in url:
            raise HTTPException(status_code=400, detail="Invalid Google Sheet URL")
        
        # Convert to CSV export URL
        if "/edit" in url:
            csv_url = url.split("/edit")[0] + "/export?format=csv"
        elif "/view" in url:
            csv_url = url.split("/view")[0] + "/export?format=csv"
        else:
            csv_url = url.rstrip('/') + "/export?format=csv"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(csv_url, headers=headers, timeout=10)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Request failed: {str(e)}")

        if response.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch sheet data (Status {response.status_code}). Ensure it is public and shared as 'Anyone with the link can view'.")
        
        df = pd.read_csv(StringIO(response.text))
        
        # Identify key columns (case-insensitive fuzzy matching)
        def find_col(keywords):
            for c in df.columns:
                if any(k in c.lower() for k in keywords):
                    return c
            return None

        emp_id_col = find_col(['intern id', 'empid', 'emp id', 'id'])
        feedback_col = find_col(['feedback', 'performance', 'comment', 'remark', 'elaborate', 'feedback'])
        
        if not emp_id_col or not feedback_col:
            found_cols = list(df.columns)
            error_msg = f"Required columns not found. We need an ID column (found: {emp_id_col or 'Missing'}) and a Feedback column (found: {feedback_col or 'Missing'}). Found columns: {found_cols}"
            raise HTTPException(status_code=400, detail=error_msg)

        sync_count = 0
        for _, row in df.iterrows():
            eid = str(row[emp_id_col]).strip()
            text = str(row[feedback_col]).strip()
            
            if eid and text and text.lower() != 'nan':
                # Upsert into feedback_collection
                feedback_collection.update_one(
                    {'EmpID': eid, 'manager_id': data.manager_id, 'batch_id': data.batch_id, 'column': 'External Sheet'},
                    {'$set': {'text': text, 'date': datetime.now().isoformat()}},
                    upsert=True
                )
                sync_count += 1
                
        return {"message": f"Successfully synced {sync_count} feedback entries", "count": sync_count}
    except Exception as e:
        if isinstance(e, HTTPException): raise e
        raise HTTPException(status_code=500, detail=str(e))
