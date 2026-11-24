import os
import json
from typing import Optional, List
from .classifier_port import EventClassifierPort
from .taxonomy import CategoryDefinition, EventClassificationResult
from .prompts import build_classification_system_prompt

class GeminiEventClassifier(EventClassifierPort):
    """
    Google Gemini LLM adapter.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name

    async def classify_event(
        self,
        name: str,
        description: Optional[str] = None,
        available_categories: Optional[List[CategoryDefinition]] = None
    ) -> EventClassificationResult:
        if not self.api_key:
            return EventClassificationResult(
                category_key="other",
                display_name="אחר",
                confidence=0.0,
                reasoning="GEMINI_API_KEY is not configured"
            )

        categories = available_categories or []
        system_prompt = build_classification_system_prompt(categories)

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=system_prompt
            )

            prompt = f"Event Name: {name}\nEvent Description: {description or 'None'}"
            response = await model.generate_content_async(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            data = json.loads(response.text)
            matched_key = data.get("category_key", "other")
            matched_cat = next((c for c in categories if c.key == matched_key), None)

            return EventClassificationResult(
                category_key=matched_key,
                display_name=matched_cat.display_name if matched_cat else None,
                confidence=float(data.get("confidence", 0.9)),
                reasoning=data.get("reasoning", "")
            )
        except Exception as e:
            return EventClassificationResult(
                category_key="other",
                display_name="אחר",
                confidence=0.0,
                reasoning=f"Gemini classification error: {str(e)}"
            )
