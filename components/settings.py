import streamlit as st
from datetime import datetime
import json
from utils.translations import get_translation

def render_settings():
    t = lambda key: get_translation(key, st.session_state.language)
    diet_options = {
        t('no_preference'): "",
        t('vegetarian'): "vegetarian",
        t('vegan'): "vegan",
        t('keto'): "keto",
        t('low_carb'): "low-carb",
        t('high_protein'): "high-protein",
        t('mediterranean'): "mediterranean",
        t('gluten_free'): "gluten-free"
    }
    goal_options = {
        t('no_goal'): "",
        t('weight_loss'): "weight-loss",
        t('muscle_gain'): "muscle-gain",
        t('energy_boost'): "energy",
        t('better_digestion'): "digestion",
        t('immune_boost'): "immunity",
        t('heart_health'): "heart-health"
    }

    st.markdown(f"### ⚙️ {t('settings')}")

    st.markdown(f"#### {t('account_info')}")

    col_set1, col_set2 = st.columns(2)

    with col_set1:
        st.text_input(
            t('username'),
            value=st.session_state.username,
            disabled=True
        )

        user_email = st.session_state.user_data.get('email', '')
        new_email = st.text_input(
            t('email'),
            value=user_email,
            placeholder=t('email_placeholder')
        )

    with col_set2:
        st.text_input(
            t('member_since'),
            value=st.session_state.user_data['created'].strftime('%Y-%m-%d')
            if isinstance(st.session_state.user_data.get('created'), datetime)
            else st.session_state.user_data.get('created', 'N/A'),
            disabled=True
        )

        if st.button(t('change_password')):
            st.info(t('change_password_coming_soon'))

    st.markdown(f"#### {t('preferences')}")

    user_prefs = st.session_state.user_data.get('preferences', {})

    col_pref1, col_pref2 = st.columns(2)

    with col_pref1:
        default_diet = st.selectbox(
            t('default_diet'),
            options=list(diet_options.keys()),
            index=0,
            help=t('default_diet_help')
        )

        default_cuisine = st.multiselect(
            t('favorite_cuisines'),
            [t('chinese'), t('western'), t('japanese'), t('korean'),
             t('thai'), t('italian'), t('mexican')],
            default=user_prefs.get('favorite_cuisines', []),
            help=t('favorite_cuisines_help')
        )

    with col_pref2:
        default_goal = st.selectbox(
            t('default_goal'),
            options=list(goal_options.keys()),
            index=0,
            help=t('default_goal_help')
        )

        newsletter = st.checkbox(
            t('subscribe_newsletter'),
            value=user_prefs.get('newsletter', False),
            help=t('newsletter_help')
        )

    if st.button(t('save_settings'), type="primary"):
        new_prefs = {
            'default_diet': diet_options[default_diet],
            'default_goal': goal_options[default_goal],
            'favorite_cuisines': default_cuisine,
            'newsletter': newsletter
        }

        st.session_state.db.update_user_preferences(st.session_state.username, new_prefs)

        if new_email != user_email:
            st.session_state.db.update_user_email(st.session_state.username, new_email)

        st.success(t('settings_saved'))
        st.balloons()

    st.markdown("---")
    st.markdown(f"#### ⚠️ {t('danger_zone')}")

    col_danger1, col_danger2, col_danger3 = st.columns(3)

    with col_danger1:
        if st.button(t('export_data'), use_container_width=True):
            user_data = {
                'user_info': st.session_state.user_data,
                'recipes': st.session_state.db.get_user_recipes(st.session_state.username, limit=1000)
            }

            st.download_button(
                label=t('download_data'),
                data=json.dumps(user_data, ensure_ascii=False, indent=2, default=str),
                file_name=f"recipe_data_{st.session_state.username}_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json"
            )

    with col_danger2:
        if st.button(t('clear_recipes'), type="secondary", use_container_width=True):
            st.warning(t('clear_recipes_warning'))

    with col_danger3:
        if st.button(t('delete_account'), type="secondary", use_container_width=True):
            st.error(t('delete_account_warning'))