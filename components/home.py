import streamlit as st
from utils.translations import get_translation

def render_home():
    t = lambda key: get_translation(key, st.session_state.language)

    st.markdown(f"# 🍳 {t('app_title')}")
    st.markdown(f"### {t('app_subtitle')}")

    st.markdown("---")

    # Feature showcase
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="recipe-card">
            <h3>🤖 {t('feature_1_title')}</h3>
            <p>{t('feature_1_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="recipe-card">
            <h3>📊 {t('feature_2_title')}</h3>
            <p>{t('feature_2_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="recipe-card">
            <h3>☁️ {t('feature_3_title')}</h3>
            <p>{t('feature_3_desc')}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f"### 🎥 {t('how_it_works')}")
    st.info(t('login_to_start'))