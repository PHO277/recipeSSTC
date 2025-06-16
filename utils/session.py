import streamlit as st # type: ignore
import os
from pathlib import Path
from mongodb_manager import MongoDBManager
import sys

def initialize_session():
    # Add project path
    sys.path.append(str(Path(__file__).parent.parent))

    # Initialize session state
    if 'db' not in st.session_state:
        mongo_uri = st.secrets.get("MONGODB_URI", os.getenv("MONGODB_URI"))
        if not mongo_uri:
            st.error("⚠️ MongoDB connection string not found. Please configure it in secrets.")
            st.stop()
        st.session_state.db = MongoDBManager(mongo_uri)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = None
    if 'language' not in st.session_state:
        st.session_state.language = 'zh'
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "generate"
    if 'recipe_data' not in st.session_state:
        st.session_state.recipe_data = None