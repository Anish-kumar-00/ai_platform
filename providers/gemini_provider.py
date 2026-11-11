from google import genai
from google.genai import types
from providers.base_provider import BaseProvider, ProviderError


class GeminiProvider(BaseProvider):
    id = "gemini"
    label = "Google (Gemini)"
    models = ["gemini-3.8-flash"]
    free_tier_note = "Free tier available with rate limits (key: aistudio.google.com)."

    @staticmethod
    def _config(system, low_thinking):
        kwargs = {"system_instruction": system or None}
        if low_thinking:
            kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="LOW")
        return types.GenerateContentConfig(**kwargs)

    def stream(self, messages, model, api_key, system=""):
        contents = [
            types.Content(
                role="model" if m["role"] == "assistant" else "user",
                parts=[types.Part(text=m["content"])],
            )
            for m in messages
        ]
        # First try with low "thinking" (faster); if unsupported, retry normally.
        for low in (True, False):
            got_text = False
            try:
                client = genai.Client(
                    api_key=api_key,
                    http_options=types.HttpOptions(timeout=120000),  # 2 min
                )
                for chunk in client.models.generate_content_stream(
                        model=model, contents=contents,
                        config=self._config(system, low)):
                    for cand in (chunk.candidates or []):
                        parts = cand.content.parts if cand.content else None
                        for part in (parts or []):
                            if part.text and not getattr(part, "thought", False):
                                got_text = True
                                yield part.text
            except Exception as e:
                msg = str(e).lower()
                if low and not got_text and (
                        "thinking" in msg or isinstance(e, (ValueError, TypeError))):
                    continue
                if "timed out" in msg or "timeout" in msg:
                    raise ProviderError(
                        "Gemini ne time par jawab nahi diya. Thodi der baad dobara try karo.") from e
                raise self.friendly_error(e) from e
            if got_text:
                return
            if not low:
                raise ProviderError("Gemini ne khaali jawab diya. Dobara try karo.")
