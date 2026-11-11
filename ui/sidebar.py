import streamlit as st
from database import db
from providers import PROVIDERS
from config.secrets_manager import get_api_key, set_session_key
from tools import project_manager


def _reset_conv():
    st.session_state.conv_id = None


def _create_project():
    name = st.session_state.get("new_project_name", "").strip()
    if name:
        st.session_state.project_id = project_manager.create_project(name)
        st.session_state.conv_id = None
        st.session_state.new_project_name = ""


def _rename_project(pid):
    name = st.session_state.get(f"rn_{pid}", "").strip()
    if name:
        db.rename_project(pid, name)


def _delete_project(pid):
    project_manager.delete_project(pid)
    st.session_state.project_id = None
    st.session_state.conv_id = None


def render_sidebar():
    with st.sidebar:
        st.title("AI Platform")

        # ---- projects ----
        projects = db.list_projects()
        names = {p["id"]: p["name"] for p in projects}
        if st.session_state.get("project_id") not in names:
            st.session_state.project_id = None
        st.selectbox("Project", [None] + list(names), key="project_id",
                     format_func=lambda i: "💬 General chat" if i is None else f"📁 {names[i]}",
                     on_change=_reset_conv)
        pid = st.session_state.project_id

        with st.expander("＋ New project"):
            st.text_input("Project name", key="new_project_name")
            st.button("Create project", on_click=_create_project, use_container_width=True)

        if pid:
            with st.expander("Manage project"):
                st.text_input("Rename", value=names[pid], key=f"rn_{pid}")
                st.button("Save name", on_click=_rename_project, args=(pid,))
                ok = st.checkbox("Confirm delete (files + chats)", key=f"delp_{pid}")
                st.button("🗑 Delete project", disabled=not ok,
                          on_click=_delete_project, args=(pid,))

        # ---- model ----
        st.subheader("Model")
        prov_id = st.selectbox("Provider", list(PROVIDERS), key="provider_id",
                               format_func=lambda i: PROVIDERS[i].label)
        prov = PROVIDERS[prov_id]
        choice = st.selectbox("Model", prov.models + ["Custom…"], key=f"model_{prov_id}")
        if choice == "Custom…":
            choice = st.text_input("Model ID", key=f"custom_{prov_id}")
        st.session_state.model = choice
        st.caption(prov.free_tier_note)

        with st.expander("API key", expanded=not get_api_key(prov_id)):
            key = st.text_input(f"{prov.label} key", type="password", key=f"keyin_{prov_id}")
            if key:
                set_session_key(prov_id, key)
            st.caption("Kept in this browser session only. For permanent keys use Streamlit Secrets.")
        st.write("✅ Key found" if get_api_key(prov_id) else "⚠️ No key")

        # ---- chats ----
        st.subheader("Chats")
        if st.button("＋ New chat", use_container_width=True):
            st.session_state.conv_id = db.create_conversation(project_id=pid)
            st.rerun()
        for conv in db.list_conversations(pid):
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
