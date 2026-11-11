import anthropic
from providers.base_provider import BaseProvider


class ClaudeProvider(BaseProvider):
    id = "claude"
    label = "Anthropic (Claude)"
    models = ["claude-sonnet-5-5", "claude-haiku-5-5", "claude-opus-5-5"]
    free_tier_note = "No free API tier; prepaid credits required. Haiku is cheapest."

    def stream(self, messages, model, api_key, system=""):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            kwargs = {"system": system} if system else {}
            with client.messages.stream(model=model, max_tokens=4096,
                                        messages=messages, **kwargs) as s:
                for text in s.text_stream:
                    yield text
        except Exception as e:
            raise self.friendly_error(e) from e
