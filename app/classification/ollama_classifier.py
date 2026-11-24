import os
import json
from typing import Optional, List
import urllib.request
from .classifier_port import EventClassifierPort
from .taxonomy import CategoryDefinition, EventClassificationResult
from .prompts import build_classification_system_prompt

class OllamaEventClassifier(EventClassifierPort):
    """
    Local LLM adapter running on-premise / localhost via Ollama (e.g. Llama 3, Mistral, Qwen).
    No external API keys, zero network data leak, completely free and private.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: str = "llama3:latest",
        timeout_seconds: int = 30
    ):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model_name = model_name or os.getenv("LLM_MODEL", "llama3:latest")
        self.timeout_seconds = timeout_seconds

    async def classify_event(
        self,
        name: str,
        description: Optional[str] = None,
        available_categories: Optional[List[CategoryDefinition]] = None
    ) -> EventClassificationResult:
        categories = available_categories or []
        system_prompt = build_classification_system_prompt(categories)
        user_prompt = f"Event Name: {name}\nEvent Description: {description or 'None'}"

        endpoint = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model_name,
            "system": system_prompt,
            "prompt": user_prompt,
            "format": "json",
            "stream": False
        }

        try:
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as response:
                result_json = json.loads(response.read().decode("utf-8"))
                response_text = result_json.get("response", "{}")
                data = json.loads(response_text)

                matched_key = data.get("category_key", "other")
                matched_cat = next((c for c in categories if c.key == matched_key), None)

                return EventClassificationResult(
                    category_key=matched_key,
                    display_name=matched_cat.display_name if matched_cat else None,
                    confidence=float(data.get("confidence", 0.9)),
                    reasoning=data.get("reasoning", "Classified by local model")
                )
        except Exception as e:
            return EventClassificationResult(
                category_key="other",
                display_name="אחר",
                confidence=0.0,
                reasoning=f"Ollama local model error: {str(e)}"
            )
