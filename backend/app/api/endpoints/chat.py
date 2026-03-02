from fastapi import APIRouter, HTTPException
from groq import Groq
import os
import json
from app.schemas.all_models import ChatQueryModel
from app.core.database import interns_collection, scores_collection, feedback_collection, batches_collection, settings_collection

router = APIRouter(prefix="/api", tags=["chat"])
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

@router.post("/chat")
async def chat(data: ChatQueryModel):
    try:
        interns = list(interns_collection.find({'manager_id': data.manager_id, 'batch_id': data.batch_id}, {'_id': 0}))
        scores = list(scores_collection.find({'manager_id': data.manager_id, 'batch_id': data.batch_id}, {'_id': 0}))
        feedbacks = list(feedback_collection.find({'manager_id': data.manager_id, 'batch_id': data.batch_id}, {'_id': 0}))
        batch = batches_collection.find_one({'batch_id': data.batch_id})
        batch_name = batch['name'] if batch else "Unknown Batch"

        score_map = {s['EmpID']: s.get('scores', {}) for s in scores}
        feedback_map = {}
        for f in feedbacks:
            eid = f['EmpID']
            if eid not in feedback_map: feedback_map[eid] = []
            feedback_map[eid].append(f"{f.get('column', 'General')}: {f['text']}")

        settings = settings_collection.find_one({"manager_id": data.manager_id, "batch_id": data.batch_id}, {"_id": 0})
        settings_context = "No custom threshold settings found. Assume standard 60% passing."
        if settings:
            settings_context = f"""
Threshold Settings for FTE Conversion:
- Highly Recommended (Green): >= {settings.get('recommended_score', 85)}% overall score.
- Borderline / Mentorship (Yellow): > {settings.get('passing_score', 60)}% and < {settings.get('recommended_score', 85)}% overall score.
- Needs Improvement / Fail (Red): <= {settings.get('passing_score', 60)}% overall score.

Subject Weightages for calculating overall score:
{json.dumps(settings.get('weightages', {}))}
"""

        context = f"Active Batch: {batch_name}\n\n{settings_context}\n\nIntern Profiles:\n"
        for i in interns:
            eid = i['EmpID']
            s = score_map.get(eid, {})
            f = feedback_map.get(eid, [])
            context += f"- {i['Name']} ({eid}):\n Scores: {json.dumps(s)}\n Feedback: {'; '.join(f)}\n\n"
        
        system_prompt = """You are an elite, highly professional L&D Data Assistant. 
Your job is to provide factual, highly accurate answers based on the provided JSON data.
When explicitly asked if an intern should be converted to FTE or what their status is, you MUST mathematically calculate their overall score using the provided Subject Weightages, and then categorize them strictly according to the Threshold Settings for FTE Conversion provided in the context.

CRITICAL FORMATTING RULES:
1. Respond in clean, well-structured Markdown.
2. Use Markdown Tables where appropriate (`| Subject | Score |`).
3. DO NOT use LaTeX, KaTeX, or complex math block delimiters (like `[ \\text{...} ]` or `\\frac{...}{...}`). 
4. Always write math in simple standard text format (e.g., `86 * 0.25 = 21.5`).
5. Use bolding for emphasis and bullet points for lists.
6. Keep your tone professional and objective. Do not invent data."""
        
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context:\n{context}\n\nQuery: {data.query}"}
            ]
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
