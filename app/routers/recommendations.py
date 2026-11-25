from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Optional, List
from app.auth import verify_jwt_token
from app.database import get_database
from app.classification.factory import get_event_classifier
from app.classification.service import EventClassificationService
from app.recommendations.retrieval import MongoCandidateRetriever
from app.recommendations.ai_scorer_llm import LLMAIScorer
from app.recommendations.service import RecommendationService
from app.recommendations.ai_scorer_port import ParticipantRecommendation

router = APIRouter(prefix="/api/recommendations", tags=["Recommendations"])

def get_recommendation_service() -> RecommendationService:
    db = get_database()
    classifier = get_event_classifier()
    class_service = EventClassificationService(classifier=classifier, db=db)
    retriever = MongoCandidateRetriever(db=db)
    scorer = LLMAIScorer()
    return RecommendationService(
        classification_service=class_service,
        retriever=retriever,
        scorer=scorer,
        db=db
    )

@router.post("/events/{event_id}", response_model=List[ParticipantRecommendation])
async def get_event_recommendations(
    event_id: str,
    top_k: int = Query(default=10, ge=1, le=50),
    group_type: Optional[str] = Query(default=None),
    rec_service: RecommendationService = Depends(get_recommendation_service),
    _user=Depends(verify_jwt_token)
):
    try:
        recommendations = await rec_service.recommend_for_event(
            event_id=event_id,
            group_type=group_type,
            top_k=top_k
        )
        return recommendations
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
