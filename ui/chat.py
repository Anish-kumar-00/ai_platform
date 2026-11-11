import streamlit as st
from database import db
from providers import PROVIDERS
from providers.base_provider import ProviderError
from config.secrets_manager import get_api_key
from tools import project_manager
from tools.file_manager import FileManager

BASE_SYSTEM = "You are a helpful senior software engineer. Use Markdown and fenced code blocks."


def _system_prompt(project):
    if not project:
        return BASE_SYSTEM
    tree = FileManager(project_manager.project_dir(project)).tree()[:3000]
    return (f"{BASE_SYSTEM}\nYou are helping with the project '{project['name']}'.\n"
            f"Current project files:\n{tree or '(empty)'}")


def render_chat(project=None):
    pid_proj = project["id"] if project else None
    if not st.session_state.get("conv_id"):
        st.session_state.conv_id = db.create_conversation(project_id=pid_proj)
    conv_id = st.session_state.conv_id

    for m in db.get_messages(conv_id):
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m["role"] == "assistant" and m["model"]:
                st.caption(f"{m['provider']} · {m['model']}")

    prompt = st.chat_input("Ask anything…")
    if not prompt:
        return

    pid, model = st.session_state.provider_id, st.session_state.get("model")
    key = get_api_key(pid)
    if not key or not model:
        st.error("Add an API key and choose a model in the sidebar.")
        return

    history = db.get_messages(conv_id)
    if not history:
        db.rename_conversation(conv_id, prompt[:40])
    db.add_message(conv_id, "user", prompt)
    with st.chat_message("user"):
        st.markdown(prompt)

    msgs = [{"role": m["role"], "content": m["content"]} for m in history]
    msgs.append({"role": "user", "content": prompt})

    ok = False
    with st.chat_message("assistant"):
        st.caption(f"Responding: {PROVIDERS[pid].label} · {model}")
        try:
            reply = st.write_stream(
                PROVIDERS[pid].stream(msgs, model, key, _system_prompt(project)))
            db.add_message(conv_id, "assistant", reply, pid, model)
            ok = True
        except ProviderError as e:
            st.error(str(e))
    if ok:
        st.rerun()
