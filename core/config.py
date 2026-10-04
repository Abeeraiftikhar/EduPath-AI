import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    # Tried in order when the primary model is overloaded (503), retired (404) or rate limited (429).
    gemini_fallback_models: tuple = tuple(
        m.strip() for m in os.getenv("GEMINI_FALLBACK_MODELS", "gemini-3.1-flash-lite,gemini-flash-lite-latest").split(",") if m.strip()
    )
    max_validation_retries: int = int(os.getenv("MAX_VALIDATION_RETRIES", "2"))

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)

settings = Settings()
