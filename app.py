import streamlit as st
from config.page_config import setup_page, load_css
from utils.session import initialize_session
from utils.translations import get_translation, LANGUAGES
from components.sidebar import render_sidebar
from components.home import render_home
from components.generate_recipe import render_generate_recipe
from components.my_recipes import render_my_recipes
from components.discover import render_discover
from components.statistics import render_statistics
from components.settings import render_settings
from components.footer import render_footer

def main():
    # Setup page configuration and CSS
    setup_page()
    load_css()

    # Initialize session state
    initialize_session()

    # Render sidebar
    render_sidebar()

    # Main content based on login status
    if not st.session_state.logged_in:
        render_home()
    else:
        # Tabs for authenticated users
        tab_list = [
            get_translation('generate_recipe', st.session_state.language),
            get_translation('my_recipes', st.session_state.language),
            get_translation('discover', st.session_state.language),
            get_translation('statistics', st.session_state.language),
            get_translation('settings', st.session_state.language)
        ]
        tabs = st.tabs(tab_list)

        with tabs[0]:
            render_generate_recipe()
        with tabs[1]:
            render_my_recipes()
        with tabs[2]:
            render_discover()
        with tabs[3]:
            render_statistics()
        with tabs[4]:
            render_settings()

    # Render footer
    render_footer()

if __name__ == "__main__":
    main()