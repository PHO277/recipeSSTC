import streamlit as st # type: ignore
import os
import random
from llm_interface import LLMInterface
from utils.translations import get_translation
from components.image_input_modal import ImageInputModal
from components.recipe_display import RecipeDisplay
import json

def render_generate_recipe():
    t = lambda key: get_translation(key, st.session_state.language)

    # 初始化图像输入模态窗口
    image_modal = ImageInputModal()

    # 初始化食谱显示组件
    recipe_display = RecipeDisplay()

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

                    actual_diet = diet_options[diet]
                    actual_goal = goal_options[goal]

                    use_simulated_output=False # 改为 True 可以使用模拟输出,方便测试

                    llm_output = None

                    if not use_simulated_output:
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

                    #simulate LLM output for testing
                    else:
                        llm_output_str= """{
                            "title": "Mediterranean Garlic Herb Chicken with Roasted Broccoli",
                            "description": "A high-protein Mediterranean dish perfect for muscle gain, featuring juicy herb-marinated chicken with garlic roasted broccoli.",
                            "ingredients": [
                                "2 large chicken breasts (6 oz each)",
                                "2 cups fresh broccoli florets",
                                "3 cloves garlic, minced",
                                "1 tbsp olive oil",
                                "1 tsp dried oregano",
                                "1/2 tsp sea salt",
                                "1/4 tsp black pepper",
                                "1/4 tsp paprika",
                                "1 tbsp lemon juice"
                            ],
                            "instructions": [
                                "Preheat oven to 400°F (200°C) and line a baking sheet with parchment paper.",
                                "In a small bowl, mix olive oil, minced garlic, oregano, salt, pepper, paprika, and lemon juice to create a marinade.",
                                "Coat chicken breasts evenly with the marinade and let sit for 10 minutes while preparing broccoli.",
                                "Toss broccoli florets with remaining marinade and spread on one side of the baking sheet.",
                                "Place chicken breasts on the other side of the baking sheet and roast for 20-25 minutes until chicken reaches 165°F internal temperature.",
                                "Let chicken rest for 5 minutes before slicing to retain juices."
                            ],
                            "nutrition": {
                                "Calories": "320 kcal",
                                "Protein": "42 g",
                                "Carbohydrates": "12 g",
                                "Fat": "11 g",
                                "Fiber": "4 g",
                                "Sugar": "3 g",
                                "Sodium": "480 mg",
                                "Vitamin A": "1200 IU",
                                "Calcium": "90 mg",
                                "Iron": "2.5 mg"
                            },
                            "serves": 2,
                            "prep_time": "15 min",
                            "cook_time": "25 min",
                            "difficulty": "Easy"
                        }"""

                        llm_output= json.loads(llm_output_str.strip())

                    st.session_state.recipe_data= llm_output

                    st.success(t('recipe_generated'))

                    recipe_display.display_full_recipe(llm_output, show_save_options=True)

                except Exception as e:
                    st.error(f"{t('generation_error')}: {str(e)}")
                    st.info(t('try_again_later'))
        elif st.session_state.recipe_data:
            # 如果已经有食谱数据，直接显示
            recipe_display.display_full_recipe(st.session_state.recipe_data, show_save_options=True)

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
            st.session_state.ingredient_input = random_ingredients
            st.rerun()
            


        if generate_btn and not ingredients:
            st.warning(t('please_enter_ingredients'))