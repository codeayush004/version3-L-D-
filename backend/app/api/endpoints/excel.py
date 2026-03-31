from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from datetime import datetime
from app.core.database import (
    interns_collection, scores_collection, subjects_collection, 
    feedback_collection, batches_collection
)

from app.api.dependencies import verify_manager_role

router = APIRouter(prefix="/api", tags=["excel"])

@router.post("/upload-interns")
async def upload_interns(
    batch_id: str = Form(...),
    file: UploadFile = File(...),
    manager_id: str = Form(None),
    token_payload: dict = Depends(verify_manager_role)
):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "admin" in roles
    m_id = token_payload['identified_username']

    if "adminviewer" in roles and not is_admin and "ldmanager" not in roles:
        raise HTTPException(status_code=403, detail="Admin viewers cannot upload excel files")
        
    if not is_admin:
        batch = batches_collection.find_one({'batch_id': batch_id, 'manager_id': {'$regex': f"^{m_id}$", '$options': 'i'}})
        if not batch:
            raise HTTPException(status_code=403, detail="Not authorized to upload data to this batch")

    try:
        contents = await file.read()
        # Read without header first to detect sub-headers
        df_raw = pd.read_excel(io.BytesIO(contents), header=None)
        
        # Combine Row 1 and Row 2 into a single header list
        header1_raw = [x if pd.notna(x) else None for x in df_raw.iloc[0].values]
        header2 = [str(x).strip() if pd.notna(x) else "" for x in df_raw.iloc[1].values]
        
        # Forward fill header1
        header1 = []
        last_h = ""
        for h in header1_raw:
            if h: last_h = str(h).strip()
            header1.append(last_h)
            
        final_headers = []
        for h1, h2 in zip(header1, header2):
            if h1 and h2:
                final_headers.append(f"{h1} ({h2})")
            else:
                final_headers.append(h2 if h2 else h1)
            
        # Re-read with the combined headers, skipping the first two rows
        df = pd.read_excel(io.BytesIO(contents), skiprows=2, header=None)
        df.columns = final_headers
        
        # Cleanup column names
        df.columns = df.columns.astype(str).str.strip()
        
        # Detect and calculate Assessment/Assignment averages if they don't exist
        if 'Assessment Average' not in df.columns:
            mcq_cols = [c for c in df.columns if 'MCQ' in c]
            if mcq_cols:
                df['Assessment Average'] = df[mcq_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
        
        if 'Assignment Average' not in df.columns:
            assn_cols = [c for c in df.columns if 'Assignment' in c]
            if assn_cols:
                df['Assignment Average'] = df[assn_cols].apply(pd.to_numeric, errors='coerce').mean(axis=1)
        
        print(f"DEBUG: Final Headers: {df.columns.tolist()}")
        if len(df) > 0:
            print(f"DEBUG: First row preview: {df.iloc[0].to_dict()}")

        col_map = {}
        for c in df.columns:
            clean_c = str(c).lower().replace(' ', '')
            if clean_c in ['empid', 'intid', 'employeeid']: col_map[c] = 'EmpID'
            elif clean_c in ['employeename', 'name']: col_map[c] = 'Name'
            elif clean_c in ['emailid', 'email', 'emailaddress']: col_map[c] = 'Email'
            elif clean_c == 'assessmentaverage': col_map[c] = 'Assessment'
            elif clean_c == 'assignmentaverage': col_map[c] = 'Assignment'
            elif clean_c == 'techviva%': col_map[c] = 'Tech Viva'
            elif clean_c == 'techdemoscore': col_map[c] = 'Tech Demo'
            elif clean_c in ['comments', 'feedback', 'mentorcomments']: col_map[c] = 'Feedback'
            elif clean_c in ['collegename', 'college']: col_map[c] = 'College'
            elif clean_c in ['coursename', 'course', 'degree']: col_map[c] = 'Degree'
            elif clean_c == 'cgpa': col_map[c] = 'CGPA'
        
        if col_map:
            df.rename(columns=col_map, inplace=True)
            
        # Drop rows where Name or Email is NaN (this removes sub-header rows and empty rows)
        if 'Email' in df.columns:
            df = df.dropna(subset=['Email'])
        if 'Name' in df.columns:
            df = df.dropna(subset=['Name'])

        df = df.reset_index(drop=True)

        # Generate fallback INT ID if not present
        if 'EmpID' not in df.columns and 'Email' in df.columns:
            df['EmpID'] = [f"INT-{str(i+1).zfill(3)}" for i in range(len(df))]
            
        required_bio = ['Name', 'Email', 'EmpID']
        if not all(col in df.columns for col in required_bio):
            raise HTTPException(status_code=400, detail=f"Excel must at least contain mappings for: {required_bio}")        
        subj_doc = subjects_collection.find_one({'manager_id': manager_id, 'batch_id': batch_id})
        existing_list = []
        existing_names = []
        
        if subj_doc and subj_doc.get('list'):
            for s in subj_doc.get('list'):
                name = s['name'] if isinstance(s, dict) else s
                if name not in existing_names:
                    existing_names.append(name)
                    existing_list.append(s if isinstance(s, dict) else {"name": s, "total_marks": 100})
                
        ignore_cols = ['manager_id', 'batch_id', 'dateofjoining', 'batch', 'mentorname', 'trainingstatus', 'fteconversiondate', 'overallscore', 'rank', 'collegename', 'college', 'coursename', 'course', 'degree', 'cgpa', 'assessment', 'assignment', 'feedback', 'techviva', 'techdemo', 'comments']
        potential_subjects = []
        for col in df.columns:
            c = col.strip()
            clean_c_lower = c.lower().replace(' ', '')
            if c in required_bio or any(x in clean_c_lower for x in ignore_cols) or clean_c_lower.startswith('unnamed:'):
                continue
            
            # User wants MCQ scores in the grid
            if '(MCQ Scores)' in c:
                potential_subjects.append(c)
                
        new_subjects_added = False
        for col in potential_subjects:
            # Clean name for the grid (e.g. "Linux - RedHat")
            clean_name = col.split('(')[0].strip()
            if clean_name not in existing_names:
                total = 100
                if '(' in col and 'Total' in col:
                    try: total = int(col.split(':')[-1].replace(')', '').strip())
                    except: total = 100
                
                existing_names.append(clean_name)
                existing_list.append({"name": clean_name, "total_marks": total})
                new_subjects_added = True
        
        if new_subjects_added or not subj_doc:
            # Explicitly clear old subjects and set new ones to prevent overlaps
            subjects_collection.update_one(
                {'batch_id': batch_id},
                {'$set': {'list': existing_list}, '$unset': {'subjects': ""}},
                upsert=True
            )

        interns_data = df.to_dict('records')
        for row in interns_data:
            emp_id = str(row['EmpID']).strip()
            intern_bio = {
                'Name': str(row['Name']).strip(),
                'Email': str(row['Email']).strip(),
                'EmpID': emp_id,
                'manager_id': manager_id,
                'batch_id': batch_id,
                'date_of_joining': str(row.get('Date of Joining', '')).strip() if pd.notna(row.get('Date of Joining', '')) else '',
                'mentor_name': str(row.get('Mentor Name', '')).strip() if pd.notna(row.get('Mentor Name', '')) else '',
                'training_status': str(row.get('Training Status', '')).strip() if pd.notna(row.get('Training Status', '')) else '',
                'fte_conversion_date': str(row.get('FTE Conversion Date', '')).strip() if pd.notna(row.get('FTE Conversion Date', '')) else '',
                'mapped_batch': str(row.get('Batch', '')).strip() if pd.notna(row.get('Batch', '')) else '',
                'college': str(row.get('College', '')).strip() if pd.notna(row.get('College', '')) else '',
                'degree': str(row.get('Degree', '')).strip() if pd.notna(row.get('Degree', '')) else '',
                'cgpa': str(row.get('CGPA', '')).strip() if pd.notna(row.get('CGPA', '')) else ''
            }
            interns_collection.update_one(
                {'EmpID': emp_id, 'batch_id': batch_id},
                {'$set': intern_bio},
                upsert=True
            )
            
            scores_to_save = {}
            for col in df.columns:
                stripped_col = col.strip()
                # ONLY process columns that we identified as Scoring columns (MCQs)
                if '(MCQ Scores)' in stripped_col:
                    clean_name = stripped_col.split('(')[0].strip()
                    val = row[col]
                    if pd.notnull(val) and (isinstance(val, (int, float, complex)) or hasattr(val, '__int__')):
                        scores_to_save[f"scores.{clean_name}"] = round(float(val), 1)
                
                # Also capture Tech Demo and Tech Viva if they were mapped
                elif stripped_col in ['Tech Demo', 'Tech Viva', 'Assessment', 'Assignment']:
                    val = row[col]
                    if pd.notnull(val) and (isinstance(val, (int, float, complex)) or hasattr(val, '__int__')):
                        scores_to_save[f"scores.{stripped_col}"] = round(float(val), 1)

            # Ensure all subjects in existing_list are initialized
            for s in existing_list:
                s_name = s['name']
                if f"scores.{s_name}" not in scores_to_save:
                    scores_to_save[f"scores.{s_name}"] = 0.0

            if scores_to_save:
                scores_collection.update_one(
                    {'EmpID': emp_id, 'batch_id': batch_id},
                    {'$set': scores_to_save},
                    upsert=True
                )
            
            # Save feedback columns
            for col in df.columns:
                clean_name = col.split('(')[0].strip()
                is_text_feedback = ('Feedback' in col or 'Comment' in col) and clean_name not in existing_names
                if is_text_feedback:
                    val = row[col]
                    if pd.notnull(val) and str(val).strip():
                        feedback_collection.update_one(
                            {
                                'EmpID': emp_id, 
                                'batch_id': batch_id,
                                'column': col
                            },
                            {'$set': {
                                'EmpID': emp_id,
                                'manager_id': manager_id,
                                'batch_id': batch_id,
                                'column': col,
                                'text': str(val).strip(),
                                'date': datetime.now().strftime("%Y-%m-%d")
                            }},
                            upsert=True
                        )
                
        return {"message": "Success"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/export-scores")
async def export_scores(manager_id: str, batch_id: str):
    try:
        interns = list(interns_collection.find({'batch_id': batch_id}, {'_id': 0}))
        scores = list(scores_collection.find({'batch_id': batch_id}, {'_id': 0}))
        subjects_doc = subjects_collection.find_one({'batch_id': batch_id}, {'_id': 0})
        subjects_list = subjects_doc.get('list', []) if subjects_doc else []
        
        scores_map = {s['EmpID']: s.get('scores', {}) for s in scores}
        
        export_data = []
        for intern in interns:
            row = {'Name': intern['Name'], 'INT ID': intern['EmpID'], 'Email': intern['Email']}
            intern_scores = scores_map.get(intern['EmpID'], {})
            for s in subjects_list:
                s_name = s['name'] if isinstance(s, dict) else s
                s_total = s['total_marks'] if isinstance(s, dict) else 100
                row[f"{s_name} (Total: {s_total})"] = intern_scores.get(s_name, 0)
            export_data.append(row)
            
        df = pd.DataFrame(export_data)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Performance Grid')
        output.seek(0)
        
        batch = batches_collection.find_one({'batch_id': batch_id})
        batch_name = batch['name'] if batch else "Batch"
        filename = f"Scores_{batch_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx"
        
        return StreamingResponse(
            output,
            media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename="{filename}"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
