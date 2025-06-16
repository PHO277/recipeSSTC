import streamlit as st
from datetime import datetime
from utils.translations import get_translation
from components.recipe_display import RecipeDisplay

def render_my_recipes():
    t = lambda key: get_translation(key, st.session_state.language)

    st.markdown(f"### 📚 {t('my_recipes')}")

    col_search1, col_search2, col_search3 = st.columns([2, 1, 1])

    with col_search1:
        search_query = st.text_input(
            "",
            placeholder=t('search_recipes'),
            label_visibility="collapsed"
        )

    with col_search2:
        sort_by = st.selectbox(
            "",
            [t('newest_first'), t('oldest_first'), t('highest_rated'), t('most_used')],
            label_visibility="collapsed"
        )

    with col_search3:
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
        filter_diet = st.selectbox(
            "",
            [t('all_diets')] + list(diet_options.keys()),
            label_visibility="collapsed"
        )

    if search_query:
        recipes = st.session_state.db.search_recipes(st.session_state.username, search_query)
    else:
        recipes = st.session_state.db.get_user_recipes(st.session_state.username)

    if recipes:
        if sort_by == t('oldest_first'):
            recipes.reverse()
        elif sort_by == t('highest_rated'):
            recipes.sort(key=lambda x: x.get('rating', 0), reverse=True)

        if filter_diet != t('all_diets'):
            recipes = [r for r in recipes if r.get('diet') == diet_options.get(filter_diet, '')]

        st.info(f"{t('found_recipes')}: {len(recipes)}")

        recipe_display = RecipeDisplay()
        for idx, recipe in enumerate(recipes):
            recipe_display.display_recipe_card(recipe, show_actions=True, key_prefix=f"recipe_{idx}_")
            
    else:
        st.info(t('no_recipes_yet'))
        if st.button(t('create_first_recipe')):
            st.session_state.active_tab = "generate"
            st.rerun()