import streamlit as st # type: ignore
from datetime import datetime
from collections import Counter
from utils.translations import get_translation

def render_statistics():
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

    st.markdown(f"### 📊 {t('statistics')}")

    stats = st.session_state.db.get_recipe_statistics(st.session_state.username)

    if stats and stats.get('total_recipes', 0) > 0:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                t('total_recipes'),
                stats.get('total_recipes', 0),
                help=t('total_recipes_help')
            )

        with col2:
            avg_rating = stats.get('avg_rating', 0)
            st.metric(
                t('avg_rating'),
                f"{avg_rating:.1f} ⭐" if avg_rating else "N/A",
                help=t('avg_rating_help')
            )

        with col3:
            diets = stats.get('most_used_diet', [])
            if diets:
                most_common_diet = max(set(diets), key=diets.count)
                diet_display = next((k for k, v in diet_options.items() if v == most_common_diet), most_common_diet)
            else:
                diet_display = "N/A"

            st.metric(
                t('favorite_diet'),
                diet_display,
                help=t('favorite_diet_help')
            )

        with col4:
            current_month_recipes = st.session_state.db.get_user_recipes_by_month(
                st.session_state.username,
                datetime.now().year,
                datetime.now().month
            ) if hasattr(st.session_state.db, 'get_user_recipes_by_month') else []

            st.metric(
                t('this_month'),
                len(current_month_recipes) if current_month_recipes else "N/A",
                help=t('this_month_help')
            )

        st.markdown("---")

        col_stat1, col_stat2 = st.columns(2)

        with col_stat1:
            st.markdown(f"### 📈 {t('recipe_trends')}")

            recent_recipes = st.session_state.db.get_user_recipes(st.session_state.username, limit=7)
            if recent_recipes:
                st.markdown(f"**{t('recent_recipes')}:**")
                for recipe in recent_recipes[:5]:
                    created = recipe['created']
                    if isinstance(created, str):
                        created = datetime.fromisoformat(created)

                    st.markdown(
                        f"- {created.strftime('%m-%d')} - "
                        f"{recipe['ingredients'][:30]}... "
                        f"{'⭐' * recipe.get('rating', 0)}"
                    )

        with col_stat2:
            st.markdown(f"### 🏷️ {t('popular_tags')}")

            all_tags = []
            all_recipes = st.session_state.db.get_user_recipes(st.session_state.username, limit=100)
            for recipe in all_recipes:
                all_tags.extend(recipe.get('tags', []))

            if all_tags:
                tag_counts = Counter(all_tags)
                st.markdown(f"**{t('most_used_tags')}:**")
                for tag, count in tag_counts.most_common(10):
                    st.markdown(f"- {tag} ({count})")

        st.markdown("---")
        st.info(t('more_analytics_coming_soon'))
    else:
        st.info(t('no_statistics_yet'))
        if st.button(t('start_cooking')):
            st.session_state.active_tab = "generate"
            st.rerun()