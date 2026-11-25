import json
from typing import List
from app.models.event import Event
from .scoring_config import CandidateMatch

def build_scorer_system_prompt() -> str:
    return """You are an expert community engagement and attendance analytics assistant.
Your task is to rank recommended candidates for an event and provide a concise, factual explanation in Hebrew (1-2 sentences) for each participant.

STRICT GROUNDING RULES (No Hallucinations):
1. The reasoning MUST be strictly grounded in the provided factual metrics (category attendance counts, diurnal time slot patterns, streak, punctuality).
2. Do NOT invent hobbies, interests, or attendance history that are not present in the data.
3. The compatibility score must be an integer between 0 and 100.
4. The reasoning text must be written in natural Hebrew.

Output strictly valid JSON with the following structure:
{
  "recommendations": [
    {
      "participant_id": "<id>",
      "score": 95,
      "reasoning": "<Hebrew factual reasoning based strictly on metrics>"
    }
  ]
}
"""

def build_scorer_user_prompt(event: Event, candidates: List[CandidateMatch]) -> str:
    candidates_data = [
        {
            "id": c.participant_id,
            "name": c.participant_name,
            "raw_score": c.total_score,
            "metrics": c.breakdown
        }
        for c in candidates
    ]

    event_data = {
        "name": event.name,
        "category": event.category or "general",
        "date": event.date.strftime("%Y-%m-%d %H:%M"),
        "time_bucket": event.time_bucket
    }

    return f"Target Event:\n{json.dumps(event_data, ensure_ascii=False, indent=2)}\n\nCandidates:\n{json.dumps(candidates_data, ensure_ascii=False, indent=2)}"
