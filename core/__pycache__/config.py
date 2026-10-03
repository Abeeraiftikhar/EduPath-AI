import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    max_validation_retries: int = int(os.getenv("MAX_VALIDATION_RETRIES", "1"))

    @property
    def gemini_configured(self) -> bool:
        return bool(self.gemini_api_key)

settings = Settings()
