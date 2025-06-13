import streamlit as st
from utils.translations import get_translation

def render_discover():
    t = lambda key: get_translation(key, st.session_state.language)
    st.markdown(f"### 🌟 {t('discover_recipes')}")
    st.info(t('discover_coming_soon'))