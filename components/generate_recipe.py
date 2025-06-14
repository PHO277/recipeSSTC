import streamlit as st # type: ignore
import os
from datetime import datetime
import random
from llm_interface import LLMInterface
from nutrition_analyzer import NutritionAnalyzer
from utils.translations import get_translation
from components.image_input_modal import ImageInputModal

def render_generate_recipe():
    t = lambda key: get_translation(key, st.session_state.language)

    # 初始化图像输入模态窗口
    image_modal = ImageInputModal()

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown(f"### 📝 {t('recipe_params')}")

        # 渲染图像输入模态窗口并获取输入的食材
        ingredient_from_image = image_modal.render_modal()

        with st.form("recipe_form", clear_on_submit=False):
            # 食材输入框 - 使用session state来保持图像识别的结果
            if 'ingredient_input' not in st.session_state:
                st.session_state.ingredient_input = ""
            
            ingredients = st.text_area(
                t('ingredients'),
                value=st.session_state.ingredient_input,
                placeholder=t('ingredients_placeholder'),
                height=100,
                help=t('ingredients_help'),
                key="ingredients_textarea"
            )

            # 更新session state
            st.session_state.ingredient_input = ingredients

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

            diet = st.selectbox(
                t('diet_preference'),
                options=list(diet_options.keys()),
                help=t('diet_help')
            )

            goal_options = {
                t('no_goal'): "",
                t('weight_loss'): "weight-loss",
                t('muscle_gain'): "muscle-gain",
                t('energy_boost'): "energy",
                t('better_digestion'): "digestion",
                t('immune_boost'): "immunity",
                t('heart_health'): "heart-health"
            }

            goal = st.selectbox(
                t('health_goal'),
                options=list(goal_options.keys()),
                help=t('goal_help')
            )

            with st.expander(t('advanced_options')):
                col_adv1, col_adv2 = st.columns(2)

                with col_adv1:
                    cuisine = st.selectbox(
                        t('cuisine_type'),
                        [t('any_cuisine'), t('chinese'), t('western'), t('japanese'),
                         t('korean'), t('thai'), t('italian'), t('mexican')]
                    )

                    cooking_time = st.select_slider(
                        t('cooking_time'),
                        options=[t('15_min'), t('30_min'), t('45_min'), t('60_min'), t('90_min')],
                        value=t('30_min')
                    )

                with col_adv2:
                    difficulty = st.select_slider(
                        t('difficulty'),
                        options=[t('easy'), t('medium'), t('hard')],
                        value=t('medium')
                    )

                    servings = st.number_input(
                        t('servings'),
                        min_value=1,
                        max_value=10,
                        value=2
                    )

            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                generate_btn = st.form_submit_button(
                    t('generate_recipe'),
                    type="primary",
                    use_container_width=True
                )
            with col_btn2:
                lucky_btn = st.form_submit_button(
                    t('feeling_lucky'),
                    use_container_width=True
                )

    with col2:
        if generate_btn and ingredients:
            with st.spinner(t('generating_recipe')):
                try:
                    api_key = st.secrets.get("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY"))
                    if not api_key:
                        st.error(t('api_key_missing'))
                        st.stop()

                    llm = LLMInterface(api_key=api_key)
                    nutrition = NutritionAnalyzer()

                    actual_diet = diet_options[diet]
                    actual_goal = goal_options[goal]

                    llm_output = llm.generate_recipe_and_nutrition(
                        ingredients,
                        actual_diet,
                        actual_goal,
                        language=st.session_state.language,
                        cuisine=cuisine if 'cuisine' in locals() else None,
                        cooking_time=cooking_time if 'cooking_time' in locals() else None,
                        difficulty=difficulty if 'difficulty' in locals() else None,
                        servings=servings if 'servings' in locals() else 2
                    )

                    st.success(t('recipe_generated'))

                    # Display recipe title
                    st.markdown(f"<h2 style='font-size: 1.8em;'>{llm_output['title']}</h2>", unsafe_allow_html=True)

                    # Display recipe description
                    st.markdown(f"### ℹ️ {t('recipe_description')}")
                    st.markdown(llm_output['description'])

                    # Display ingredients
                    st.markdown(f"### 🥕 {t('ingredients')}")
                    for ingredient in llm_output['ingredients']:
                        st.markdown(f"- {ingredient}")

                    # Display instructions
                    st.markdown(f"### 🍳 {t('instructions')}")
                    for i, step in enumerate(llm_output['instructions'], 1):
                        st.markdown(f"{i}. {step}")
                        
                    # Display nutrition facts
                    st.markdown(f"### 🥗 {t('nutrition_facts')}")
                    nutrition_info = nutrition.parse_nutrition(llm_output)
                    nutrition_dict = {}
                    for line in nutrition_info.split('\n'):
                        if ':' in line:
                            key, value = line.split(':', 1)
                            # Normalize the key by removing spaces and leading/trailing characters
                            cleaned_key = key.strip().strip('-').replace(' ', '')
                            nutrition_dict[cleaned_key] = value.strip()

                    print(nutrition_dict)  # Debugging line to check nutrition_dict content

                    nutrition_items = [
                        ("🔥", t('calories'), nutrition_dict.get("Calories", "N/A")),
                        ("🥩", t('protein'), nutrition_dict.get("Protein", "N/A")),
                        ("🥑", t('fat'), nutrition_dict.get("Fat", "N/A")),
                        ("🌾", t('carbs'), nutrition_dict.get("Carbohydrates", "N/A")),
                        ("🌱", t('fiber'), nutrition_dict.get("Fiber", "N/A")),
                        ("🍬", t('sugar'), nutrition_dict.get("Sugar", "N/A")),
                        ("🧂", t('sodium'), nutrition_dict.get("Sodium", "N/A")),
                        ("🧬", t('vitamin_a'), nutrition_dict.get("VitaminA", "N/A")),  # Normalized key
                        ("🦴", t('calcium'), nutrition_dict.get("Calcium", "N/A")),
                        ("🩺", t('iron'), nutrition_dict.get("Iron", "N/A"))
                    ]

                    for icon, label, value in nutrition_items:
                        nutrition_html = f'''
                        <div class="nutrition-item" style="background-color: #e6f3ff; padding: 10px; margin: 5px; border-radius: 5px; display: inline-block;">
                            <span style="font-size: 1.5em;">{icon}</span>
                            <strong>{label}:</strong> {value}
                        </div>
                        '''
                        st.markdown(nutrition_html, unsafe_allow_html=True)

                    # Display additional recipe information
                    st.markdown(f"**{t('serves')}**: {llm_output['serves']}")
                    st.markdown(f"**{t('prep_time')}**: {llm_output['prep_time']}")
                    st.markdown(f"**{t('cook_time')}**: {llm_output['cook_time']}")
                    st.markdown(f"**{t('difficulty')}**: {llm_output['difficulty']}")

                    st.markdown("---")
                    st.markdown(f"### 💾 {t('save_options')}")

                    col_save1, col_save2 = st.columns(2)

                    with col_save1:
                        rating = st.slider(t('rate_recipe'), 0, 5, 3, help=t('rate_help'))
                        tags_input = st.text_input(
                            t('add_tags'),
                            placeholder=t('tags_placeholder'),
                            help=t('tags_help')
                        )

                    with col_save2:
                        notes = st.text_area(
                            t('notes'),
                            placeholder=t('notes_placeholder'),
                            height=100
                        )

                    col_action1, col_action2, col_action3 = st.columns(3)

                    with col_action1:
                        if st.button(t('save_recipe'), type="primary", use_container_width=True):
                            recipe_data = {
                                "title": llm_output['title'],
                                "description": llm_output['description'],
                                "ingredients": llm_output['ingredients'],
                                "instructions": llm_output['instructions'],
                                "nutrition": nutrition_info,
                                "serves": llm_output['serves'],
                                "prep_time": llm_output['prep_time'],
                                "cook_time": llm_output['cook_time'],
                                "difficulty": llm_output['difficulty'],
                                "rating": rating,
                                "tags": [tag.strip() for tag in tags_input.split(',') if tag.strip()],
                                "notes": notes,
                                "cuisine": cuisine if 'cuisine' in locals() else "",
                                "diet": diet,
                                "goal": goal
                            }

                            recipe_id = st.session_state.db.save_recipe(st.session_state.username, recipe_data)
                            st.success(t('recipe_saved'))
                            st.balloons()

                    with col_action2:
                        recipe_text = f"""
                            {t('recipe')}
                            {'=' * 50}

                            {t('recipe_title')}: {llm_output['title']}

                            {t('recipe_description')}
                            {'-' * 50}
                            {llm_output['description']}

                            {t('ingredients')}
                            {'-' * 50}
                            {chr(10).join(f'- {ingredient}' for ingredient in llm_output['ingredients'])}

                            {t('instructions')}
                            {'-' * 50}
                            {chr(10).join(f'{i}. {step}' for i, step in enumerate(llm_output['instructions'], 1))}

                            {t('nutrition_facts')}
                            {'-' * 50}
                            {nutrition_info}

                            ---
                            {t('serves')}: {llm_output['serves']}
                            {t('prep_time')}: {llm_output['prep_time']}
                            {t('cook_time')}: {llm_output['cook_time']}
                            {t('difficulty')}: {llm_output['difficulty']}
                            {t('generated_on')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                            {t('ingredients')}: {ingredients}
                            {t('diet_preference')}: {diet}
                            {t('health_goal')}: {goal}
"""
                        st.download_button(
                            label=t('download_recipe'),
                            data=recipe_text.encode('utf-8'),
                            file_name=f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True
                        )

                    with col_action3:
                        if st.button(t('share_recipe'), use_container_width=True):
                            st.info(t('share_coming_soon'))

                except Exception as e:
                    st.error(f"{t('generation_error')}: {str(e)}")
                    st.info(t('try_again_later'))

        if lucky_btn:
            random_ingredients = random.choice([
                "鸡胸肉, 西兰花, 胡萝卜",
                "豆腐, 香菇, 青菜",
                "三文鱼, 芦笋, 柠檬",
                "牛肉, 土豆, 洋葱",
                "虾, 黄瓜, 番茄"
            ])

            st.info(f"{t('lucky_ingredients')}: {random_ingredients}")
            st.info(t('click_generate_with_these'))

        if generate_btn and not ingredients:
            st.warning(t('please_enter_ingredients'))