from typing import List, Optional
from bson import ObjectId
from app.models.event import Event
from app.classification.service import EventClassificationService
from app.recommendations.retrieval import MongoCandidateRetriever
from app.recommendations.ai_scorer_port import AIScorerPort, ParticipantRecommendation

class RecommendationService:
    """
    End-to-End Recommendation Orchestrator:
    1. Loads target Event.
    2. Ensures Event has category (Slice 2).
    3. Retrieves top matching candidates from MongoDB (Slice 4).
    4. Evaluates and explains recommendations via Grounded AI Scorer (Slice 5).
    """

    def __init__(
        self,
        classification_service: EventClassificationService,
        retriever: MongoCandidateRetriever,
        scorer: AIScorerPort,
        db=None
    ):
        self.classification_service = classification_service
        self.retriever = retriever
        self.scorer = scorer
        self.db = db

    async def recommend_for_event(
        self,
        event_id: str,
        group_type: Optional[str] = None,
        top_k: int = 10
    ) -> List[ParticipantRecommendation]:
        # 1. Fetch event from DB
        event = None
        if self.db is not None:
            doc = await self.db["events"].find_one({"_id": ObjectId(event_id)})
            if doc:
                event = Event.model_validate(doc)

        if not event:
            raise ValueError(f"Event with ID '{event_id}' not found")

        # 2. Classify event if needed
        if not event.category:
            res = await self.classification_service.get_or_classify_event(event, group_id=group_type)
            event.category = res.category_key

        # 3. Retrieve candidates
        candidates = await self.retriever.get_top_candidates_from_db(
            event=event,
            group_type=group_type,
            top_k=top_k
        )

        # 4. Generate AI reasoning and final scores
        recommendations = await self.scorer.generate_recommendations(event, candidates)

        return recommendations
