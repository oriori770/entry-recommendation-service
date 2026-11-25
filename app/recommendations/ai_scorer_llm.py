import os
import json
import urllib.request
from typing import List, Optional
from app.models.event import Event
from .scoring_config import CandidateMatch
from .ai_scorer_port import AIScorerPort, ParticipantRecommendation
from .ai_prompts import build_scorer_system_prompt, build_scorer_user_prompt
from .ai_scorer_mock import MockAIScorer

class LLMAIScorer(AIScorerPort):
    """
    LLM Scorer supporting local Ollama models or Cloud APIs (OpenAI, Gemini).
    Falls back gracefully to MockAIScorer upon network or parsing issues.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower().strip()
        self.model_name = model_name or os.getenv("LLM_MODEL")
        self.fallback = MockAIScorer()

    async def generate_recommendations(
        self,
        event: Event,
        candidates: List[CandidateMatch]
    ) -> List[ParticipantRecommendation]:
        if not candidates:
            return []

        # If configured as mock, use deterministic mock immediately
        if self.provider == "mock":
            return await self.fallback.generate_recommendations(event, candidates)

        system_prompt = build_scorer_system_prompt()
        user_prompt = build_scorer_user_prompt(event, candidates)

        try:
            # 1. Ollama / Local Model
            if self.provider in ("ollama", "local"):
                base_url = (os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
                endpoint = f"{base_url}/api/generate"
                payload = {
                    "model": self.model_name or "llama3:latest",
                    "system": system_prompt,
                    "prompt": user_prompt,
                    "format": "json",
                    "stream": False
                }
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    raw_res = json.loads(resp.read().decode("utf-8"))
                    text = raw_res.get("response", "{}")
                    data = json.loads(text)
                    return self._map_llm_response(data, candidates)

            # 2. OpenAI
            elif self.provider == "openai":
                from openai import AsyncOpenAI
                client = AsyncOpenAI(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    base_url=os.getenv("OPENAI_BASE_URL")
                )
                res = await client.chat.completions.create(
                    model=self.model_name or "gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    response_format={"type": "json_object"}
                )
                text = res.choices[0].message.content or "{}"
                data = json.loads(text)
                return self._map_llm_response(data, candidates)

            # 3. Gemini
            elif self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
                model = genai.GenerativeModel(
                    model_name=self.model_name or "gemini-1.5-flash",
                    system_instruction=system_prompt
                )
                res = await model.generate_content_async(
                    user_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                data = json.loads(res.text)
                return self._map_llm_response(data, candidates)

        except Exception:
            pass

        # Fallback on any failure
        return await self.fallback.generate_recommendations(event, candidates)

    def _map_llm_response(
        self,
        llm_data: dict,
        candidates: List[CandidateMatch]
    ) -> List[ParticipantRecommendation]:
        recs_map = {
            r.get("participant_id"): r
            for r in llm_data.get("recommendations", [])
        }
        candidates_by_id = {c.participant_id: c for c in candidates}

        results: List[ParticipantRecommendation] = []
        for c in candidates:
            llm_rec = recs_map.get(c.participant_id)
            if llm_rec:
                score = int(min(100, max(0, llm_rec.get("score", 70))))
                reasoning = llm_rec.get("reasoning", "")
            else:
                score = 70
                reasoning = "מומלץ על סמך התאמה כללית"

            results.append(
                ParticipantRecommendation(
                    participant_id=c.participant_id,
                    participant_name=c.participant_name,
                    phone=c.phone,
                    city=c.city,
                    group_type=c.group_type,
                    score=score,
                    reasoning=reasoning,
                    breakdown=c.breakdown
                )
            )

        return sorted(results, key=lambda r: r.score, reverse=True)
