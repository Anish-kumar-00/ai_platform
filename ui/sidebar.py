import streamlit as st
from database import db
from providers import PROVIDERS
from config.secrets_manager import get_api_key, set_session_key


def render_sidebar():
    with st.sidebar:
        st.title("AI Platform")
        if st.button("＋ New chat", use_container_width=True):
            st.session_state.conv_id = db.create_conversation()
            st.rerun()

        st.subheader("Model")
        pid = st.selectbox("Provider", list(PROVIDERS), key="provider_id",
                           format_func=lambda i: PROVIDERS[i].label)
        prov = PROVIDERS[pid]
        choice = st.selectbox("Model", prov.models + ["Custom…"], key=f"model_{pid}")
        if choice == "Custom…":
            choice = st.text_input("Model ID", key=f"custom_{pid}")
        st.session_state.model = choice
        st.caption(prov.free_tier_note)

        with st.expander("API key", expanded=not get_api_key(pid)):
            key = st.text_input(f"{prov.label} key", type="password", key=f"keyin_{pid}")
            if key:
                set_session_key(pid, key)
            st.caption("Kept in this browser session only. For permanent keys use Streamlit Secrets.")
        st.write("✅ Key found" if get_api_key(pid) else "⚠️ No key")

        st.subheader("Chats")
        for conv in db.list_conversations():
            cols = st.columns([5, 1, 1])
            if cols[0].button(conv["title"][:28], key=f"c{conv['id']}", use_container_width=True):
                st.session_state.conv_id = conv["id"]
                st.rerun()
            if cols[1].button("✏️", key=f"r{conv['id']}"):
                st.session_state.renaming = conv["id"]
            if cols[2].button("🗑", key=f"d{conv['id']}"):
                db.delete_conversation(conv["id"])
                if st.session_state.get("conv_id") == conv["id"]:
                    st.session_state.conv_id = None
                st.rerun()
        rid = st.session_state.get("renaming")
        if rid:
            new = st.text_input("New title", key="rename_box")
            if st.button("Save title") and new.strip():
                db.rename_conversation(rid, new.strip())
                st.session_state.renaming = None
                st.rerun()
