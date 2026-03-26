from fastapi import APIRouter, HTTPException
from app.core.database import batches_collection, interns_collection

router = APIRouter(prefix="/api", tags=["global"])

@router.get("/global-stats")
async def get_global_stats(manager_id: str):
    try:
        batches = list(batches_collection.find({}, {'_id': 0}))
        interns = interns_collection.count_documents({})

        return {
            "total_batches": len(batches),
            "total_interns_across_org": interns,
            "batches": batches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
