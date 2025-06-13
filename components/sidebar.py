import streamlit as st
from datetime import datetime
from utils.translations import get_translation, LANGUAGES

def render_sidebar():
    t = lambda key: get_translation(key, st.session_state.language)

    with st.sidebar:
        # Language selection
        st.markdown("### 🌐 Language / 语言")
        selected_lang = st.selectbox(
            "",
            options=list(LANGUAGES.keys()),
            format_func=lambda x: LANGUAGES[x]['name'],
            index=list(LANGUAGES.keys()).index(st.session_state.language),
            label_visibility="collapsed"
        )

        if selected_lang != st.session_state.language:
            st.session_state.language = selected_lang
            if st.session_state.logged_in:
                st.session_state.db.update_user_language(st.session_state.username, selected_lang)
            st.rerun()

        st.markdown("---")

        # Authentication or user info
        if not st.session_state.logged_in:
            from components.auth import render_auth
            render_auth()
        else:
            # User info
            st.markdown(f"### 👤 {t('user_info')}")

            col1, col2 = st.columns([1, 3])
            with col1:
                st.markdown(
                    f'<div class="user-avatar">{st.session_state.username[0].upper()}</div>',
                    unsafe_allow_html=True
                )
            with col2:
                st.markdown(f"**{st.session_state.username}**")
                member_since = st.session_state.user_data.get('created', datetime.utcnow())
                if isinstance(member_since, str):
                    member_since = datetime.fromisoformat(member_since)
                st.caption(f"{t('member_since')} {member_since.strftime('%Y-%m')}")

            # User statistics
            stats = st.session_state.db.get_recipe_statistics(st.session_state.username)
            if stats:
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(t('total_recipes'), stats.get('total_recipes', 0))
                with col2:
                    avg_rating = stats.get('avg_rating', 0)
                    if avg_rating:
                        st.metric(t('avg_rating'), f"{avg_rating:.1f} ⭐")

            st.markdown("---")

            # Quick actions
            st.markdown(f"### ⚡ {t('quick_actions')}")

            if st.button(f"➕ {t('new_recipe')}", use_container_width=True):
                st.session_state.active_tab = "generate"

            if st.button(f"📚 {t('my_recipes')}", use_container_width=True):
                st.session_state.active_tab = "recipes"

            if st.button(f"⚙️ {t('settings')}", use_container_width=True):
                st.session_state.active_tab = "settings"

            st.markdown("---")

            # Logout
            if st.button(f"🚪 {t('logout')}", use_container_width=True, type="secondary"):
                for key in ['logged_in', 'username', 'user_data']:
                    st.session_state[key] = None
                st.rerun()