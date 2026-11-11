from providers.openai_provider import OpenAIProvider
from providers.gemini_provider import GeminiProvider
from providers.claude_provider import ClaudeProvider

# To add a provider: create a class, then add it here.
PROVIDERS = {p.id: p() for p in (GeminiProvider, ClaudeProvider, OpenAIProvider)}
