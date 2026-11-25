import pytest
from datetime import datetime
from bson import ObjectId
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.models.event import Event
from app.models.participant import Participant
from app.recommendations.scoring_config import CandidateMatch
from app.recommendations.ai_scorer_port import ParticipantRecommendation
import hmac
import hashlib
import json
import base64

def generate_test_jwt(secret: str = "default_secret_for_dev") -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"userId": "admin_123", "role": "admin"}

    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{h_b64}.{p_b64}".encode()
    sig = hmac.new(secret.encode(), signing_input, hashlib.sha256).digest()
    s_b64 = base64.urlsafe_b64encode(sig).decode().rstrip("=")

    return f"{h_b64}.{p_b64}.{s_b64}"

client = TestClient(app)

def test_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "entry-recommendation-service"

def test_tenant_categories_endpoint_unauthenticated_allowed():
    res = client.get("/api/tenants/temimim/categories")
    assert res.status_code == 200
    categories = res.json()
    assert len(categories) > 0
    assert any(c["key"] == "football" for c in categories)

def test_protected_recommendations_rejects_missing_token():
    res = client.post("/api/recommendations/events/507f1f77bcf86cd799439011")
    assert res.status_code == 401
    assert "Missing or invalid Authorization header" in res.json()["detail"]

def test_protected_recommendations_rejects_invalid_token():
    res = client.post(
        "/api/recommendations/events/507f1f77bcf86cd799439011",
        headers={"Authorization": "Bearer invalid.token.signature"}
    )
    assert res.status_code == 401

@pytest.mark.asyncio
async def test_full_recommendation_flow_e2e():
    token = generate_test_jwt()
    event_id = str(ObjectId())

    dummy_recs = [
        ParticipantRecommendation(
            participant_id="p1",
            participant_name="יוסי כהן",
            score=95,
            reasoning="השתתף ב-10 אירועי כדורגל ונמצא ברצף",
            breakdown={"category_attendances": 10}
        )
    ]

    with patch("app.routers.recommendations.RecommendationService.recommend_for_event", new_callable=AsyncMock) as mock_rec:
        mock_rec.return_value = dummy_recs

        res = client.post(
            f"/api/recommendations/events/{event_id}",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["participant_name"] == "יוסי כהן"
        assert data[0]["score"] == 95
        assert "השתתף ב-10 אירועי כדורגל" in data[0]["reasoning"]
