import streamlit as st
from database import db
from ui.sidebar import render_sidebar
from ui.chat import render_chat

st.set_page_config(page_title="AI Platform", page_icon="🤖", layout="wide")
db.init_db()
render_sidebar()
render_chat()
