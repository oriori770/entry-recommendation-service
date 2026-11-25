from fastapi import APIRouter
from app.database import get_database

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    db_status = "connected"
    try:
        db = get_database()
        await db.command("ping")
    except Exception as e:
        db_status = f"disconnected: {str(e)}"

    return {
        "status": "ok",
        "service": "entry-recommendation-service",
        "database": db_status
    }
