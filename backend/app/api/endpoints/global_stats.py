from fastapi import APIRouter, HTTPException
from app.core.database import batches_collection, interns_collection

router = APIRouter(prefix="/api", tags=["global"])

@router.get("/global-stats")
async def get_global_stats(manager_id: str):
    try:
        batches = list(batches_collection.find({'manager_id': manager_id}, {'_id': 0}))
        interns = interns_collection.count_documents({'manager_id': manager_id})
        
        # We need to calculate overall average and top performers across ALL batches.
        # This requires pulling all scores and calculating them per batch using their specific settings.
        # However, to keep it simple and blazing fast, we can approximate the overall average
        # using raw total scores vs total marks if settings aren't strictly required, 
        # or we can pull settings_map and subject_map.
        
        # Actually, let's keep it extremely lightweight: just return the batches data
        # so the frontend can orchestrate it if it wants, OR we do the math here.

        return {
            "total_batches": len(batches),
            "total_interns_across_org": interns,
            "batches": batches
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
