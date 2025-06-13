import streamlit as st
from datetime import datetime
from utils.translations import get_translation

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

        for idx, recipe in enumerate(recipes):
            created = recipe['created']
            if isinstance(created, str):
                created = datetime.fromisoformat(created)

            with st.expander(
                    f"{created.strftime('%Y-%m-%d')} | "
                    f"{recipe['ingredients'][:50]}... | "
                    f"{'⭐' * recipe.get('rating', 0)}"
            ):
                col_info1, col_info2 = st.columns([3, 1])

                with col_info1:
                    if recipe.get('tags'):
                        tags_html = ''.join([f'<span class="tag">{tag}</span>' for tag in recipe['tags']])
                        st.markdown(tags_html, unsafe_allow_html=True)

                    info_items = []
                    if recipe.get('cuisine'):
                        info_items.append(f"🍽️ {recipe['cuisine']}")
                    if recipe.get('cooking_time'):
                        info_items.append(f"⏱️ {recipe['cooking_time']}")
                    if recipe.get('difficulty'):
                        info_items.append(f"📊 {recipe['difficulty']}")
                    if recipe.get('servings'):
                        info_items.append(f"👥 {recipe['servings']} {t('servings')}")

                    if info_items:
                        st.markdown(" | ".join(info_items))

                    st.markdown(f"**{t('ingredients')}**: {recipe['ingredients']}")

                    if recipe.get('notes'):
                        st.markdown(f"**{t('notes')}**: {recipe['notes']}")

                with col_info2:
                    if st.button(f"🗑️ {t('delete')}", key=f"del_{recipe['_id']}"):
                        if st.session_state.db.delete_recipe(str(recipe['_id'])):
                            st.success(t('recipe_deleted'))
                            st.rerun()

                    if st.button(f"📤 {t('share')}", key=f"share_{recipe['_id']}"):
                        st.info(t('share_coming_soon'))

                st.markdown("---")
                st.markdown(f"### {t('recipe_content')}")
                st.markdown(recipe.get('recipe_text', recipe.get('recipe', '')))

                st.markdown(f"### {t('nutrition_info')}")
                st.text(recipe.get('nutrition_info', 'N/A'))
    else:
        st.info(t('no_recipes_yet'))
        if st.button(t('create_first_recipe')):
            st.session_state.active_tab = "generate"
            st.rerun()