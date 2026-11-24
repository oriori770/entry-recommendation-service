import os
import json
from typing import Optional, List
from .classifier_port import EventClassifierPort
from .taxonomy import CategoryDefinition, EventClassificationResult
from .prompts import build_classification_system_prompt

class OpenAIEventClassifier(EventClassifierPort):
    """
    OpenAI-compatible LLM adapter (supports OpenAI, Azure, Groq, Ollama, LocalAI, vLLM).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        base_url: Optional[str] = None
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")

    async def classify_event(
        self,
        name: str,
        description: Optional[str] = None,
        available_categories: Optional[List[CategoryDefinition]] = None
    ) -> EventClassificationResult:
        categories = available_categories or []
        system_prompt = build_classification_system_prompt(categories)

        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

            user_content = f"Event Name: {name}\nEvent Description: {description or 'None'}"
            response = await client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )

            raw_text = response.choices[0].message.content or "{}"
            data = json.loads(raw_text)

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
                reasoning=f"OpenAI classification error: {str(e)}"
            )
