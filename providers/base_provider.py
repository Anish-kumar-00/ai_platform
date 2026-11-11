from abc import ABC, abstractmethod
from typing import Iterator


class ProviderError(Exception):
    """User-friendly error raised by any provider."""


class BaseProvider(ABC):
    id: str = ""
    label: str = ""
    models: list = []
    free_tier_note: str = ""

    @abstractmethod
    def stream(self, messages: list, model: str, api_key: str,
               system: str = "") -> Iterator[str]:
        """Yield text chunks. messages = [{'role': 'user'|'assistant', 'content': str}]"""

    @staticmethod
    def friendly_error(exc: Exception) -> ProviderError:
        text = str(exc)
        low = text.lower()
        code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
        if code in (401, 403) or "api key" in low or "authentication" in low:
            return ProviderError("Invalid or missing API key.")
        if code == 429 or "rate" in low or "quota" in low:
            return ProviderError("Rate limit or quota reached. Wait a bit, or switch provider/model.")
        if "credit" in low or "billing" in low or code == 402:
            return ProviderError("Insufficient credits. Add credits or switch provider.")
        return ProviderError(f"Provider error: {text[:300]}")
