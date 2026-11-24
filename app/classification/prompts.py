from typing import List
from .taxonomy import CategoryDefinition

def build_classification_system_prompt(categories: List[CategoryDefinition]) -> str:
    cat_descriptions = "\n".join([
        f"- key: '{c.key}', label: '{c.display_name}', description: '{c.description}'"
        for c in categories if c.is_active
    ])

    return f"""You are an expert event categorization assistant.
Select EXACTLY ONE category key from the available tenant categories below that best fits the event.

Available Categories:
{cat_descriptions}

Respond strictly with valid JSON:
{{
  "category_key": "<selected key from above>",
  "confidence": <float 0.0 to 1.0>,
  "reasoning": "<short reasoning in Hebrew or English>"
}}
"""
