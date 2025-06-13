import streamlit as st
from utils.translations import get_translation

def render_auth():
    t = lambda key: get_translation(key, st.session_state.language)
    st.markdown(f"### 🔐 {t('user_auth')}")

    auth_mode = st.radio(
        "",
        [t('login'), t('register')],
        label_visibility="collapsed"
    )

    if auth_mode == t('login'):
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input(t('username'), placeholder=t('username_placeholder'))
            password = st.text_input(t('password'), type="password", placeholder=t('password_placeholder'))
            col1, col2 = st.columns(2)
            with col1:
                login_btn = st.form_submit_button(t('login'), type="primary", use_container_width=True)
            with col2:
                demo_btn = st.form_submit_button(t('demo_login'), use_container_width=True)

            if login_btn and username and password:
                success, user_data = st.session_state.db.verify_user(username, password)
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.session_state.user_data = user_data
                    st.session_state.language = user_data.get('language', 'zh')
                    st.success(t('login_success'))
                    st.balloons()
                    st.rerun()
                else:
                    st.error(t('login_failed'))

            if demo_btn:
                success, user_data = st.session_state.db.verify_user("demo", "demo123")
                if success:
                    st.session_state.logged_in = True
                    st.session_state.username = "demo"
                    st.session_state.user_data = user_data
                    st.info(t('demo_login_info'))
                    st.rerun()

    else:  # Register
        with st.form("register_form", clear_on_submit=True):
            new_username = st.text_input(t('username'), placeholder=t('username_placeholder'))
            new_email = st.text_input(t('email'), placeholder=t('email_placeholder'))
            new_password = st.text_input(t('password'), type="password", placeholder=t('password_placeholder'))
            confirm_password = st.text_input(t('confirm_password'), type="password")

            agree_terms = st.checkbox(t('agree_terms'))

            register_btn = st.form_submit_button(t('register'), type="primary", use_container_width=True)

            if register_btn:
                if not agree_terms:
                    st.error(t('must_agree_terms'))
                elif not new_username or len(new_username) < 3:
                    st.error(t('username_too_short'))
                elif new_password != confirm_password:
                    st.error(t('password_mismatch'))
                elif len(new_password) < 6:
                    st.error(t('password_too_short'))
                else:
                    success, message = st.session_state.db.create_user(
                        new_username,
                        new_password,
                        st.session_state.language,
                        new_email
                    )
                    if success:
                        st.success(t('register_success'))
                        if not st.session_state.db.get_user("demo"):
                            st.session_state.db.create_user("demo", "demo123", "zh", "demo@example.com")
                    else:
                        st.error(message)