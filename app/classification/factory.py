import os
from typing import Optional
from .classifier_port import EventClassifierPort
from .mock_classifier import MockEventClassifier
from .gemini_classifier import GeminiEventClassifier
from .openai_classifier import OpenAIEventClassifier
from .ollama_classifier import OllamaEventClassifier

def get_event_classifier(
    provider: Optional[str] = None,
    model_name: Optional[str] = None,
    base_url: Optional[str] = None
) -> EventClassifierPort:
    """
    Factory creating an EventClassifierPort based on environment or tenant preferences.
    Supported Providers:
      - 'ollama' / 'local': Local offline model running via Ollama (e.g. Llama 3, Mistral, Qwen)
      - 'mock': Rule-based fast deterministic classifier (zero API cost, tests)
      - 'gemini': Google Gemini models (e.g. gemini-1.5-flash)
      - 'openai': OpenAI models or any OpenAI-compatible API (Azure, Groq, vLLM, LMStudio)
    """
    selected_provider = (provider or os.getenv("LLM_PROVIDER", "mock")).lower().strip()

    if selected_provider in ("ollama", "local"):
        model = model_name or os.getenv("LLM_MODEL", "llama3:latest")
        url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        return OllamaEventClassifier(base_url=url, model_name=model)

    elif selected_provider == "gemini":
        model = model_name or os.getenv("LLM_MODEL", "gemini-1.5-flash")
        return GeminiEventClassifier(model_name=model)

    elif selected_provider == "openai":
        model = model_name or os.getenv("LLM_MODEL", "gpt-4o-mini")
        url = base_url or os.getenv("OPENAI_BASE_URL")
        return OpenAIEventClassifier(model_name=model, base_url=url)

    elif selected_provider == "mock":
        return MockEventClassifier()

    else:
        return MockEventClassifier()
