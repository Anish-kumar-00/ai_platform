import streamlit as st
from database import db
from ui.sidebar import render_sidebar
from ui.chat import render_chat
from ui.project_workspace import render_workspace

st.set_page_config(page_title="AI Platform", page_icon="🤖", layout="wide")
db.init_db()
render_sidebar()

project = db.get_project(st.session_state.project_id) if st.session_state.get("project_id") else None

if project:
    view = st.radio("View", ["💬 Chat", "📁 Files"], horizontal=True,
                    label_visibility="collapsed", key="view")
    if view == "📁 Files":
        render_workspace(project)
    else:
        render_chat(project)
else:
    render_chat(None)
