import json
from typing import Type, TypeVar
from pydantic import BaseModel
from core.config import settings

T = TypeVar("T", bound=BaseModel)

class GeminiProvider:
    def __init__(self):
        if not settings.gemini_api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        try:
            from google import genai
        except ImportError as exc:
            raise RuntimeError("Install google-genai to use Gemini.") from exc
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": schema,
                "temperature": 0.2,
            },
        )
        data = response.parsed if hasattr(response, "parsed") and response.parsed else json.loads(response.text)
        return schema.model_validate(data)
