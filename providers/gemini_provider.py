from google import genai
from google.genai import types
from providers.base_provider import BaseProvider, ProviderError


class GeminiProvider(BaseProvider):
    id = "gemini"
    label = "Google (Gemini)"
    models = ["gemini-3.8-flash"]
    free_tier_note = "Free tier available with rate limits (key: aistudio.google.com)."

    def stream(self, messages, model, api_key, system=""):
        got_text = False
        try:
            client = genai.Client(
                api_key=api_key,
                http_options=types.HttpOptions(timeout=60000),  # 60 sec
            )
            contents = [
                types.Content(
                    role="model" if m["role"] == "assistant" else "user",
                    parts=[types.Part(text=m["content"])],
                )
                for m in messages
            ]
            cfg = types.GenerateContentConfig(system_instruction=system or None)
            for chunk in client.models.generate_content_stream(
                    model=model, contents=contents, config=cfg):
                for cand in (chunk.candidates or []):
                    parts = cand.content.parts if cand.content else None
                    for part in (parts or []):
                        if part.text and not getattr(part, "thought", False):
                            got_text = True
                            yield part.text
        except Exception as e:
            raise self.friendly_error(e) from e
        if not got_text:
            raise ProviderError("Gemini ne khaali jawab diya. Dobara try karo ya dusra model chuno.")
