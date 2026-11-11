import os
import streamlit as st

ENV_NAMES = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "claude": "ANTHROPIC_API_KEY",
}


def get_api_key(provider_id: str):
    """Priority: session input > Streamlit secrets > environment."""
    session = st.session_state.get("keys", {}).get(provider_id)
    if session:
        return session
    name = ENV_NAMES[provider_id]
    try:
        if name in st.secrets and st.secrets[name]:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def set_session_key(provider_id: str, key: str) -> None:
    st.session_state.setdefault("keys", {})[provider_id] = key.strip()
