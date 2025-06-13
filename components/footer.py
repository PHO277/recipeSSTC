import streamlit as st
from utils.translations import get_translation

def render_footer():
    t = lambda key: get_translation(key, st.session_state.language)
    st.markdown("---")
    footer_cols = st.columns([2, 1, 1, 1])

    with footer_cols[0]:
        st.markdown(
            f"© 2024 Smart Recipe Generator | "
            f"{t('made_with')} ❤️ | "
            f"{t('version')} 1.0.0"
        )

    with footer_cols[1]:
        st.markdown(f"[{t('privacy_policy')}](#)")

    with footer_cols[2]:
        st.markdown(f"[{t('terms_of_service')}](#)")

    with footer_cols[3]:
        st.markdown(f"[{t('contact_us')}](#)")