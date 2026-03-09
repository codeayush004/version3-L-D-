from fastapi import APIRouter, HTTPException
from app.core.database import interns_collection, scores_collection, feedback_collection, subjects_collection, settings_collection
import os
import json
from groq import Groq

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/{emp_id}")
async def get_report(emp_id: str, manager_id: str, batch_id: str):
    try:
        intern = interns_collection.find_one({'EmpID': emp_id, 'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0})
        score_doc = scores_collection.find_one({'EmpID': emp_id, 'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0})
        feedbacks = list(feedback_collection.find({'EmpID': emp_id, 'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0}))
        
        subjects_doc = subjects_collection.find_one({'manager_id': manager_id, 'batch_id': batch_id}, {'_id': 0})
        subjects_list = subjects_doc.get('list', []) if subjects_doc else []
        
        # Generate AI Summary
        score_map = score_doc.get('scores', {}) if score_doc else {}
        context = f"Intern: {intern['Name']} ({emp_id})\nScores: {json.dumps(score_map)}\nFeedback: {'; '.join([f['text'] for f in feedbacks])}"
        
        ai_summary = "AI Summary not available."
        try:
            completion = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": "You are a professional L&D Assistant. Provide a concise (2-3 sentences) performance summary and one recommendation for this intern."},
                    {"role": "user", "content": f"Context:\n{context}"}
                ]
            )
            ai_summary = completion.choices[0].message.content
        except Exception:
            pass

        settings = settings_collection.find_one({'manager_id': manager_id, 'batch_id': batch_id})
        weightages = settings.get('weightages', {}) if settings else {}
        
        all_scores_docs = list(scores_collection.find({'manager_id': manager_id, 'batch_id': batch_id}))
        
        def calculate_score(s_doc):
            total = 0
            s_map = s_doc.get('scores', {})
            if weightages:
                for subj in subjects_list:
                    sName = subj['name'] if isinstance(subj, dict) else subj
                    sTotal = subj['total_marks'] if isinstance(subj, dict) else 100
                    w = weightages.get(sName)
                    if w:
                        total += (s_map.get(sName, 0) / sTotal) * w
            else:
                for subj in subjects_list:
                    sName = subj['name'] if isinstance(subj, dict) else subj
                    total += s_map.get(sName, 0)
            return total

        intern_totals = []
        for doc in all_scores_docs:
            intern_totals.append({'EmpID': doc.get('EmpID'), 'total': calculate_score(doc)})
        
        intern_totals.sort(key=lambda x: x['total'], reverse=True)
        
        rank = 1
        for idx, item in enumerate(intern_totals):
            if item['EmpID'] == emp_id:
                rank = idx + 1
                break
        total_interns = len(intern_totals)

        return {
            "intern": intern,
            "scores": score_map,
            "feedbacks": feedbacks,
            "subjects": subjects_list,
            "ai_summary": ai_summary,
            "rank": rank,
            "total_interns": total_interns
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
