import json
from typing import List
from app.models.event import Event
from .scoring_config import CandidateMatch

def build_scorer_system_prompt() -> str:
    return """אתה עוזר מומחה לניתוח נוכחות וקשרי קהילה.
תפקידך לדרג מועמדים מומלצים לאירוע ולנפק נימוק תמציתי ומנומק בעברית (משפט עד שניים) לכל משתתף.

חוקי ברזל למניעת הזיות (Strict Grounding):
1. הנימוק חייב להתבסס אך ורק על הנתונים העובדתיים שנמסרו (מוני השתתפויות בקטגוריה, שעות פעילות, רצף, וכו').
2. אין להמציא תחומי עניין או השתתפויות שלא מופיעים בנתונים.
3. ציון ההתאמה (score) חייב להיות מספר שלם בין 0 ל-100.

עליך להחזיר JSON תקין במבנה הבא:
{
  "recommendations": [
    {
      "participant_id": "...",
      "score": 95,
      "reasoning": "נימוק בעברית מבוסס עובדות"
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
        "category": event.category or "כללי",
        "date": event.date.strftime("%Y-%m-%d %H:%M"),
        "time_bucket": event.time_bucket
    }

    return f"אירוע יעד:\n{json.dumps(event_data, ensure_ascii=False, indent=2)}\n\nמועמדים:\n{json.dumps(candidates_data, ensure_ascii=False, indent=2)}"
