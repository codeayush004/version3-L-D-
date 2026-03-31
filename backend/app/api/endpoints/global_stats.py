from fastapi import APIRouter, HTTPException, Depends
from app.api.dependencies import verify_manager_role
from app.core.database import batches_collection, interns_collection

router = APIRouter(prefix="/api", tags=["global"])

@router.get("/global-stats")
async def get_global_stats(active_department: str = "Data Ops", token_payload: dict = Depends(verify_manager_role)):
    roles = [r.lower() for r in token_payload.get("roles", [])]
    is_admin = "adminviewer" in roles or "admin" in roles
    m_id = token_payload['identified_username']

    query = {}
    if not is_admin:
        query["manager_id"] = {'$regex': f"^{m_id}$", '$options': 'i'}
        
    if active_department:
        if active_department.lower() == "data ops":
            query['$or'] = [{'department': 'Data Ops'}, {'department': {'$exists': False}}]
        else:
            query['department'] = active_department

    try:
        batches = list(batches_collection.find(query, {'_id': 0}))
        interns = interns_collection.count_documents(query)

        return {
            "total_batches": len(batches),
            "total_interns_across_org": interns,
            "batches": batches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
