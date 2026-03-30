from app.api.dependencies import verify_manager_role
from fastapi import APIRouter, HTTPException, Depends

router = APIRouter(prefix="/api", tags=["global"])

@router.get("/global-stats")
async def get_global_stats(manager_id: str = "dev@example.com", active_department: str = "Data Ops"):
    query = {"manager_id": "dev@example.com"}
    
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
