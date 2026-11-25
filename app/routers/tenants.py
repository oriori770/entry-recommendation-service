from fastapi import APIRouter, Depends, Query
from typing import Optional, List
from app.database import get_database
from app.classification.taxonomy import CategoryDefinition
from app.classification.service import EventClassificationService
from app.classification.factory import get_event_classifier
from app.profiles.backfill import BackfillService
from app.auth import verify_jwt_token

router = APIRouter(prefix="/api", tags=["Tenants & Profiles"])

@router.get("/tenants/{group_id}/categories", response_model=List[CategoryDefinition])
async def get_tenant_categories(group_id: str):
    db = get_database()
    class_service = EventClassificationService(classifier=get_event_classifier(), db=db)
    categories = await class_service.get_tenant_categories(group_id)
    return categories

@router.post("/profiles/backfill")
async def trigger_backfill(
    group_id: Optional[str] = Query(default=None),
    _user=Depends(verify_jwt_token)
):
    db = get_database()
    class_service = EventClassificationService(classifier=get_event_classifier(), db=db)
    backfill_service = BackfillService(classification_service=class_service, db=db)
    count = await backfill_service.backfill_all_participants(group_id=group_id)
    return {"status": "success", "participants_updated": count}
