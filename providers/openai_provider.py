from openai import OpenAI
from providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    id = "openai"
    label = "OpenAI (ChatGPT)"
    models = ["gpt-4o-mini", "gpt-4o"]
    free_tier_note = "No free API tier; prepaid credits required."

    def stream(self, messages, model, api_key, system=""):
        try:
            client = OpenAI(api_key=api_key)
            msgs = ([{"role": "system", "content": system}] if system else []) + messages
            resp = client.chat.completions.create(model=model, messages=msgs, stream=True)
            for chunk in resp:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            raise self.friendly_error(e) from e
