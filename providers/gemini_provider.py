from google import genai
from google.genai import types
from providers.base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    id = "gemini"
    label = "Google (Gemini)"
    models = ["gemini-2.5-flash", "gemini-2.5-pro"]
    free_tier_note = "Free tier available with rate limits (key: aistudio.google.com)."

    def stream(self, messages, model, api_key, system=""):
        try:
            client = genai.Client(api_key=api_key)
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
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            raise self.friendly_error(e) from e
