import json
import re
import time
from typing import Type, TypeVar
from pydantic import BaseModel
from core.config import settings

T = TypeVar("T", bound=BaseModel)


class ProviderError(RuntimeError):
    """A failure with a short, user-friendly message. `details` holds the raw cause for an expander."""

    def __init__(self, message: str, details: str = ""):
        super().__init__(message)
        self.details = details


def friendly_error(exc: Exception) -> ProviderError:
    """Translate raw SDK errors into messages a non-technical user can act on."""
    raw = f"{type(exc).__name__}: {exc}"
    low = raw.lower()
    if any(k in low for k in ("429", "quota", "resource_exhausted", "rate limit")):
        msg = "The Gemini free-tier quota or rate limit was reached. Wait a minute and try again."
    elif any(k in low for k in ("api key", "api_key", "permission_denied", "401", "403", "unauthenticated")):
        msg = "Gemini rejected the API key. Check GEMINI_API_KEY."
    elif "404" in low or "not_found" in low or "no longer available" in low:
        msg = "The configured Gemini model is unavailable. Set GEMINI_MODEL to a current model (e.g. gemini-flash-latest)."
    elif any(k in low for k in ("timeout", "timed out", "deadline", "connection", "unavailable", "503")):
        msg = "Could not reach Gemini (network problem or timeout)."
    elif isinstance(exc, (json.JSONDecodeError, ValueError)):
        msg = "Gemini returned malformed data that did not match the course schema."
    else:
        msg = "Gemini could not complete the request."
    return ProviderError(msg, raw)


def retry_delay(exc: Exception, attempt: int, cap: float = 45.0) -> float:
    """Seconds to wait before retrying. Honors the 'retry in 13.7s' hint Gemini sends on rate limits."""
    match = re.search(r"retry in ([\d.]+)s", str(exc), re.IGNORECASE)
    if match:
        return min(float(match.group(1)) + 1, cap)
    return float(2 ** (attempt - 1))


class GeminiProvider:
    MAX_ATTEMPTS = 4

    def __init__(self):
        if not settings.gemini_api_key:
            raise ProviderError("GEMINI_API_KEY is not configured. Add it to .env or Streamlit secrets.")
        try:
            from google import genai
        except ImportError as exc:
            raise ProviderError("The google-genai package is not installed.", str(exc)) from exc
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.models = [settings.gemini_model, *settings.gemini_fallback_models]
        self.model = self.models[0]

    def generate_structured(self, prompt: str, schema: Type[T]) -> T:
        """Call Gemini, retrying transient and malformed-JSON failures. Each retry moves to the next
        model in the fallback list, so one overloaded or retired model does not break generation."""
        last_error = None
        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.models[(attempt - 1) % len(self.models)],
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": schema,
                        "temperature": 0.2,
                    },
                )
                data = response.parsed if getattr(response, "parsed", None) else json.loads(response.text)
                return schema.model_validate(data)
            except Exception as exc:  # SDK raises many types; all are translated below
                last_error = exc
                if attempt < self.MAX_ATTEMPTS:
                    time.sleep(retry_delay(exc, attempt))
        raise friendly_error(last_error)
