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
        # Step 1: Intent Classification (Two-Step Pipeline)
        router_prompt = """
You are a query classifier. Determine if the user is asking about a specific individual or the whole batch.
If individual, extract the name or EmpID.
Output ONLY valid JSON, nothing else:
{"intent": "individual" | "batch", "identifier": "Name or ID" | null}
"""
        try:
            intent_res = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": router_prompt},
                    {"role": "user", "content": data.query}
                ],
                temperature=0.1
            )
            intent_text = intent_res.choices[0].message.content.strip()
            # Clean up potential markdown formatting from LLM
            if intent_text.startswith("```"):
                lines = intent_text.split('\n')
                intent_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else intent_text
            intent_data = json.loads(intent_text)
        except Exception as e:
            # Fallback to fetching everything if classification fails
            intent_data = {"intent": "batch", "identifier": None}

        # Step 2: Targeted Database Fetch
        intern_query = {'manager_id': data.manager_id, 'batch_id': data.batch_id}
        query_matched_specific = False
        interns = []
        scores = []
        feedbacks = []
        
        if intent_data.get("intent") == "individual" and intent_data.get("identifier"):
            identifier = intent_data["identifier"]
            intern_query['$or'] = [
                {'EmpID': identifier}, 
                {'Name': {'$regex': identifier, '$options': 'i'}}
            ]
            
            # Fetch matching intern first to get exact EmpIDs for scores/feedback correlation
            matching_interns = list(interns_collection.find(intern_query, {'_id': 0}))
            if matching_interns:
                if len(matching_interns) > 1:
                    # Instant short-circuit if multiple names collide
                    names_and_ids = ", ".join([f"**{i['Name']}** ({i['EmpID']})" for i in matching_interns])
                    return {"response": f"I found multiple interns matching that name: {names_and_ids}. Could you please specify which one you are asking about by providing their exact ID?"}

                interns = matching_interns
                matched_emp_ids = [i['EmpID'] for i in matching_interns]
                sf_query = {'manager_id': data.manager_id, 'batch_id': data.batch_id, 'EmpID': {'$in': matched_emp_ids}}
                scores = list(scores_collection.find(sf_query, {'_id': 0}))
                feedbacks = list(feedback_collection.find(sf_query, {'_id': 0}))
                query_matched_specific = True

        if not query_matched_specific:
            # Fallback to batch-wide query if intent was batch, or if the individual was not found
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
- Highly Recommended (Green): >= {settings.get('recommended_score', 75)}% overall score.
- Borderline / Mentorship (Yellow): > {settings.get('passing_score', 60)}% and < {settings.get('recommended_score', 75)}% overall score.
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
        
        system_prompt = """You are an elite, highly professional L&D Data Assistant helping a Manager analyze their interns' performance. 
Your job is to provide factual, highly accurate answers based on the provided JSON data.

CRITICAL INSTRUCTIONS FOR GIVING RECOMMENDATIONS & INSIGHTS:
1. When asked about specific scores (e.g., Tech Viva, Assignment), you MUST clearly state those requested scores.
2. ALWAYS include the intern's Overall Score and their Category (Green/Yellow/Red) in your response, even if they only asked about a specific subject, to provide full context.
3. If relevant feedback exists for the intern, briefly summarize or include the most important points.
4. When asked if an intern should be converted to FTE, you MUST calculate their overall score internally based on the weightages. DO NOT show the long mathematical calculation to the user.
5. Structure your answer clearly. Use bullet points for different data points (Specific Score requested, Overall Score, Category, Feedback).
6. If asked to compare or list multiple interns, use a clean Markdown Table. 
   - DO NOT include a 'Requested Score' column if the user did not ask for a specific score.
   - Example 1 (No specific score asked): `| Intern | Overall Score | Category | Feedback |`
   - Example 2 (Tech target asked): `| Intern | Tech Viva Score | Overall Score | Category | Feedback |`

CRITICAL FORMATTING RULES:
1. Keep the output comprehensive but easy to read.
2. DO NOT use LaTeX, KaTeX, or complex math block delimiters. 
3. DO NOT output the step-by-step mathematical reasoning. Provide the final numbers directly.
4. Use bolding for emphasis."""
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if getattr(data, 'history', None):
            for msg in data.history[-6:]:
                role = "assistant" if msg.get("role") == "ai" else "user"
                messages.append({"role": role, "content": msg.get("text", "")})
                
        messages.append({"role": "user", "content": f"Context:\n{context}\n\nQuery: {data.query}"})
        
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages
        )
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
