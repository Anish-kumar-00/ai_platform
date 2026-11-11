import time

from google import genai
from google.genai import types
from providers.base_provider import BaseProvider, ProviderError


def _is_busy(e: Exception) -> bool:
    msg = str(e).lower()
    return any(k in msg for k in ("503", "unavailable", "high demand", "overloaded"))


class GeminiProvider(BaseProvider):
    id = "gemini"
    label = "Google (Gemini)"
    models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]
    free_tier_note = "Free tier available with rate limits (key: aistudio.google.com)."

    @staticmethod
    def _config(system, low_thinking):
        kwargs = {"system_instruction": system or None}
        if low_thinking:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="LOW")
        return types.GenerateContentConfig(**kwargs)

    def _once(self, contents, model, api_key, system, low):
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=40000),  # 40 sec per try
        )
        for chunk in client.models.generate_content_stream(
                model=model, contents=contents, config=self._config(system, low)):
            for cand in (chunk.candidates or []):
                parts = cand.content.parts if cand.content else None
                for part in (parts or []):
                    if part.text and not getattr(part, "thought", False):
                        yield part.text

    def stream(self, messages, model, api_key, system=""):
        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages
        ]
        low = True  # low "thinking" first (faster); fall back if unsupported
        for attempt in range(4):
            got_text = False
            try:
                for text in self._once(contents, model, api_key, system, low):
                    got_text = True
                    yield text
                if got_text:
                    return
                if not low:
                    raise ProviderError("Gemini ne khaali jawab diya. Dobara try karo.")
                low = False
                continue
            except ProviderError:
                raise
            except Exception as e:
                if got_text:
                    raise self.friendly_error(e) from e
                msg = str(e).lower()
                if low and ("thinking" in msg or isinstance(e, (ValueError, TypeError))):
                    low = False
                    continue
                timed_out = "timed out" in msg or "timeout" in msg
                if (_is_busy(e) or timed_out) and attempt < 2:
                    time.sleep(2 * (attempt + 1))  # short pause, then retry
                    continue
                if timed_out:
                    raise ProviderError(
                        "Gemini ne time par jawab nahi diya. Sidebar se dusra model "
                        "(gemini-3.7-flash ya gemini-3.5-flash-lite) chuno ya thodi der baad try karo.") from e
                raise self.friendly_error(e) from e
        raise ProviderError(
            "Gemini abhi busy hai (Google ki taraf se). Dusra model chuno ya 1-2 minute baad try karo.")
