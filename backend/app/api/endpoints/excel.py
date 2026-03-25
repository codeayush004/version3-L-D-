from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import io
import pandas as pd
from datetime import datetime
from app.core.database import (
    interns_collection, scores_collection, subjects_collection, 
    feedback_collection, batches_collection
)

router = APIRouter(prefix="/api", tags=["excel"])

@router.post("/upload-interns")
async def upload_interns(
    manager_id: str = Form(...),
    batch_id: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # Check for sub-headers to calculate Missing Averages
        try:
            if 'MCQ Scores' in str(df.iloc[0].values) or 'Assignment Scores' in str(df.iloc[0].values):
                mcq_cols = [c for c in df.columns if str(df[c].iloc[0]).strip() == 'MCQ Scores']
                assn_cols = [c for c in df.columns if str(df[c].iloc[0]).strip() == 'Assignment Scores']
                
                if mcq_cols:
                    df['Assessment Average'] = df[mcq_cols].iloc[1:].apply(pd.to_numeric, errors='coerce').mean(axis=1)
                if assn_cols:
                    df['Assignment Average'] = df[assn_cols].iloc[1:].apply(pd.to_numeric, errors='coerce').mean(axis=1)
        except Exception:
            pass
            
        # Map Identifiers and Core Aggregates
        df.columns = df.columns.astype(str).str.strip()
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
            elif clean_c == 'comments': col_map[c] = 'Feedback'
        
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
                
        ignore_cols = ['manager_id', 'batch_id', 'dateofjoining', 'batch', 'mentorname', 'trainingstatus', 'fteconversiondate', 'overallscore', 'rank']
        potential_subjects = []
        for col in df.columns:
            c = col.strip()
            clean_c_lower = c.lower().replace(' ', '')
            if c in required_bio or clean_c_lower in ignore_cols or clean_c_lower.startswith('unnamed:'):
                continue
            clean_name = c.split('(')[0].strip()
            is_text_feedback = ('Feedback' in clean_name or 'Comment' in clean_name) and clean_name not in existing_names
            if not is_text_feedback:
                potential_subjects.append(c)
                
        new_subjects_added = False
        for col in potential_subjects:
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
            subjects_collection.update_one(
                {'manager_id': manager_id, 'batch_id': batch_id},
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
                'mapped_batch': str(row.get('Batch', '')).strip() if pd.notna(row.get('Batch', '')) else ''
            }
            interns_collection.update_one(
                {'EmpID': emp_id, 'manager_id': manager_id, 'batch_id': batch_id},
                {'$set': intern_bio},
                upsert=True
            )
            
            scores_to_save = {}
            for col in df.columns:
                stripped_col = col.strip()
                clean_name = stripped_col.split('(')[0].strip()
                if clean_name in [s['name'] for s in existing_list]:
                    val = row[col]
                    if pd.notnull(val) and (isinstance(val, (int, float, complex)) or hasattr(val, '__int__')):
                        scores_to_save[f"scores.{clean_name}"] = round(float(val), 1)

            # Ensure all initialized subjects have at least a 0 score if missing from Excel
            for subject_name in existing_names:
                if f"scores.{subject_name}" not in scores_to_save:
                    scores_to_save[f"scores.{subject_name}"] = 0.0

            if scores_to_save:
                scores_collection.update_one(
                    {'EmpID': emp_id, 'manager_id': manager_id, 'batch_id': batch_id},
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
                                'manager_id': manager_id, 
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
        interns = list(interns_collection.find({'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0}))
        scores = list(scores_collection.find({'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0}))
        subjects_doc = subjects_collection.find_one({'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0})
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
