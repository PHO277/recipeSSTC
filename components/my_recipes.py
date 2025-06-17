import streamlit as st
from datetime import datetime
from utils.translations import get_translation
from components.recipe_display import RecipeDisplay

def render_my_recipes():
    t = lambda key: get_translation(key, st.session_state.language)

    # Check if we're viewing a specific recipe
    if 'viewing_recipe' in st.session_state and st.session_state.viewing_recipe:
        _display_single_recipe(st.session_state.viewing_recipe)
        return

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

        st.markdown("<hr style='margin-top: 10px;'/>", unsafe_allow_html=True)

        # Display recipe thumbnails in a more compact way
        for idx, recipe in enumerate(recipes):
            _display_recipe_thumbnail(recipe, idx)
            
    else:
        st.info(t('no_recipes_yet'))
        if st.button(t('create_first_recipe')):
            st.session_state.active_tab = "generate"
            st.rerun()

def _display_recipe_thumbnail(recipe, idx):
    """Display a recipe as a compact clickable thumbnail card"""
    t = lambda key: get_translation(key, st.session_state.language)
    
    # Create a card-like container with reduced padding
    with st.container():
        # Handle creation date
        created = recipe.get('created')
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except:
                created = datetime.now()
        elif not isinstance(created, datetime):
            created = datetime.now()
        
        # Build title - use ingredients if no title
        title = recipe.get('title', '')
        if not title:
            ingredients = recipe.get('ingredients', [])
            if isinstance(ingredients, list):
                title = ', '.join(ingredients[:3]) + ('...' if len(ingredients) > 3 else '')
            else:
                title = str(ingredients)[:50] + ('...' if len(str(ingredients)) > 50 else '')
        
        # Display rating stars if available
        rating_stars = ''
        if recipe.get('rating', 0) > 0:
            rating_stars = f"{'⭐' * recipe.get('rating', 0)}"
        
        # Create columns for layout - main content and actions
        col1, col2, col3 = st.columns([10, 1,1])
        
        with col1:
            # First row: Title and metadata on the same line
            title_col, meta_col = st.columns([4, 2])
            
            with title_col:
                st.markdown(f"**{title}**", unsafe_allow_html=True)
            
            with meta_col:
                st.caption(f"{created.strftime('%Y-%m-%d')} {rating_stars}")
            
            # Second row: Ingredients preview
            ingredients = recipe.get('ingredients', [])
            if isinstance(ingredients, list):
                ingredients_text = ', '.join(ingredients[:3]) + ('...' if len(ingredients) > 3 else '')
            else:
                ingredients_text = str(ingredients)[:100] + ('...' if len(str(ingredients)) > 100 else '')
            
            st.markdown(f"<div style='margin-top:-10px;'><small><i>{ingredients_text}</i></small></div>", unsafe_allow_html=True)
            
            # Third row: Tags
            if recipe.get('tags'):
                tags_html = ''.join([f'<span style="background-color: #e1f5fe; padding: 2px 8px; border-radius: 10px; margin-right: 4px; display: inline-block; font-size: 0.7em; margin-top: 4px;">{tag}</span>' for tag in recipe['tags']])
                st.markdown(f"<div style='margin-top:-8px;'>{tags_html}</div>", unsafe_allow_html=True)
        
        with col2:
            # Action buttons stacked vertically
            if st.button(t('view'), key=f"view_{idx}"):
                st.session_state.viewing_recipe = recipe
                st.rerun()
            
            
        with col3:
            # Delete button
            if st.button("🗑️", key=f"delete_{idx}"):
                if st.session_state.db.delete_recipe(str(recipe['_id'])):
                    st.success(t('recipe_deleted'))
                    st.rerun() 
         
        
        # Reduced spacing between recipes
        #st.markdown("<div style='margin-top:-10px;'></div>", unsafe_allow_html=True)
        st.divider()


def _display_single_recipe(recipe):
    """Display a single recipe with back button and actions"""
    t = lambda key: get_translation(key, st.session_state.language)
    
    # Create action buttons at the top
    col1, col2, col3,col4 = st.columns([1, 1, 1,7])
    
    with col1:
        if st.button("← " + t('back_to_list'),use_container_width=True):
            del st.session_state.viewing_recipe
            st.rerun()
    
    with col2:
        if st.button("🗑️ " + t('delete'),use_container_width=True):
            if st.session_state.db.delete_recipe(str(recipe['_id'])):
                st.success(t('recipe_deleted'))
                del st.session_state.viewing_recipe
                st.rerun()
    
    with col3:
        if st.button("📤 " + t('share'),use_container_width=True):
            st.info(t('share_coming_soon'))
    
    # Display the full recipe
    recipe_display = RecipeDisplay()
    recipe_display.display_full_recipe(recipe, show_save_options=False)