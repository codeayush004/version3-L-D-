import os
import json
from groq import Groq
from pydantic import BaseModel
from app.api.dependencies import verify_manager_role
from app.schemas.all_models import ChatQueryModel
from fastapi import APIRouter, HTTPException, Depends
from app.core.database import interns_collection, scores_collection, feedback_collection, batches_collection, settings_collection, chat_history_collection
from bson import ObjectId
from datetime import datetime
from app.analytics.engine import AnalyticsEngine

router = APIRouter(prefix="/api", tags=["chat"])
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

@router.get("/chat/sessions")
async def get_chat_sessions(batch_id: str):
    match_query = {'batch_id': batch_id, 'manager_id': "dev@example.com"}

    try:
        # Group messages by session_id and get the first user message as the title
        sessions = list(chat_history_collection.aggregate([
            {'$match': match_query},
            {'$sort': {'timestamp': 1}},
            {'$group': {
                '_id': '$session_id',
                'title': {'$first': '$query'},
                'last_updated': {'$last': '$timestamp'}
            }},
            {'$sort': {'last_updated': -1}}
        ]))
        return [{"session_id": s['_id'], "title": s['title'], "last_updated": s['last_updated']} for s in sessions]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/session/{session_id}")
async def get_chat_messages(session_id: str):
    try:
        msgs = list(chat_history_collection.find({'session_id': session_id}).sort('timestamp', 1))
        # Format for frontend: [{role: 'user'|'ai', text: string}]
        formatted = []
        for m in msgs:
            formatted.append({'role': 'user', 'text': m['query']})
            formatted.append({'role': 'ai', 'text': m['response']})
        return formatted
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SessionUpdateModel(BaseModel):
    title: str

@router.put("/chat/session/{session_id}")
async def update_session_title(session_id: str, data: SessionUpdateModel):
    try:
        chat_history_collection.update_many(
            {'session_id': session_id},
            {'$set': {'title': data.title}}
        )
        return {"message": "Session title updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    try:
        chat_history_collection.delete_many({'session_id': session_id})
        return {"message": "Session deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=dict)
async def chat_endpoint(data: ChatQueryModel):
    m_id = "dev@example.com"
    try:
        session_id = data.session_id or str(ObjectId())
        
        # Step 1: Intent Classification (Two-Step Pipeline)
        router_prompt = """
You are a query classifier. Determine if the user is asking about:
1. A specific individual (name or EmpID).
2. The current active batch.
4. Analytical questions about college performance, conversion trends, degree correlations, or cross-batch insights.

Output ONLY valid JSON:
{"intent": "individual" | "batch" | "global" | "analytics", "identifier": "Name or ID" | null}
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
        intern_query = {'batch_id': data.batch_id}
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
                sf_query = {'batch_id': data.batch_id, 'EmpID': {'$in': matched_emp_ids}}
                scores = list(scores_collection.find(sf_query, {'_id': 0}))
                feedbacks = list(feedback_collection.find(sf_query, {'_id': 0}))
                query_matched_specific = True

        global_context = ""
        if intent_data.get("intent") == "global":
            global_context = AnalyticsEngine.get_organization_summary(data.manager_id)
            
            # For GLOBAL intent, we do NOT load individual intern details to save tokens.
            interns = []
            scores = []
            feedbacks = []
            batch_name = "Organization-Wide Analytics"
        elif intent_data.get("intent") == "analytics":
            # Generate Deep Insights + Include Batch Statistics for Comparison
            org_summary = AnalyticsEngine.get_organization_summary(data.manager_id)
            college_perf = AnalyticsEngine.get_college_performance(data.manager_id)
            conversion_trends = AnalyticsEngine.get_conversion_stats(data.manager_id)
            academic_corr = AnalyticsEngine.get_academic_correlation(data.manager_id)
            top_performers = AnalyticsEngine.get_top_performers(data.manager_id)
            
            global_context = f"""
{org_summary}

ADVANCED ANALYTICS CONTEXT:
1. {college_perf}
2. {conversion_trends}
3. {academic_corr}
4. {top_performers}
"""
            # Keep batch info available
            interns = []
            scores = []
            feedbacks = []
            batch_name = "Cross-Batch Organizational Analytics"
        else:
            # For Individual or Batch intent, we load full details as before
            if not query_matched_specific:
                interns = list(interns_collection.find({'batch_id': data.batch_id}, {'_id': 0}))
                scores = list(scores_collection.find({'batch_id': data.batch_id}, {'_id': 0}))
                feedbacks = list(feedback_collection.find({'batch_id': data.batch_id}, {'_id': 0}))
            
            batch = batches_collection.find_one({'batch_id': data.batch_id})
            batch_name = batch['name'] if batch else "Unknown Batch"

        score_map = {s['EmpID']: s.get('scores', {}) for s in scores}
        feedback_map = {}
        for f in feedbacks:
            eid = f['EmpID']
            if eid not in feedback_map: feedback_map[eid] = []
            feedback_map[eid].append(f"{f.get('column', 'General')}: {f['text']}")

        settings = settings_collection.find_one({"batch_id": data.batch_id}, {"_id": 0})
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
        
        system_prompt = f"""
You are an expert Performance Auditor.
{f"You are currently analyzing {batch_name}." if intent_data.get("intent") not in ["global", "analytics"] else "You are performing a Cross-Batch Organizational Audit."}
{global_context}

Your job is to provide factual, highly accurate answers based on the provided data. 
If the user asks to compare batches, use the ORGANIZATION-WIDE SUMMARY provided in the context.

CRITICAL INSTRUCTIONS FOR GIVING RECOMMENDATIONS & INSIGHTS:
1. When asked about specific scores (e.g., Tech Viva, Assignment), you MUST clearly state those requested scores.
2. ALWAYS include the intern's Overall Score and their Category (Green/Yellow/Red) in your response, even if they only asked about a specific subject, to provide full context.
3. If relevant feedback exists for the intern, briefly summarize or include the most important points.
4. When asked if an intern should be converted to FTE, you MUST calculate their overall score internally based on the weightages. DO NOT show the long mathematical calculation to the user.
5. Structure your answer clearly. Use bullet points for different data points (Specific Score requested, Overall Score, Category, Feedback).
6. When asked to compare or list multiple interns, or summarize by college, use a clean Markdown Table. 
   - TRIPLE-CHECK the numbers: If the context says '11/54 converted', your table MUST say '11/54'. DO NOT hallucinate '11/11'.
   - If the user asks for "Top 5 Interns", use the provided "Top Performers Across All Batches" list directly.
   - DO NOT include a 'Requested Score' column if the user did not ask for a specific score.
   - Example (College Stats): `| College | Avg Score | Intern Count | FTE Conversion (✔/Total) | Overall Category |`
   - Example (Intern Detail): `| Intern | Overall Score | Category | Feedback |`

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
        response_text = completion.choices[0].message.content
        
        # Save to MongoDB
        chat_history_collection.insert_one({
            "session_id": session_id,
            "manager_id": data.manager_id,
            "batch_id": data.batch_id,
            "query": data.query,
            "response": response_text,
            "timestamp": datetime.now()
        })
        
        return {"response": response_text, "session_id": session_id}
    except Exception as e:
        print(f"CHAT_ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
