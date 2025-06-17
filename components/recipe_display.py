import streamlit as st
from datetime import datetime
from utils.translations import get_translation
from nutrition_analyzer import NutritionAnalyzer

class RecipeDisplay:
    def __init__(self):
        self.t = lambda key: get_translation(key, st.session_state.language)
    
    def display_full_recipe(self, recipe_data, show_save_options=True):
        """显示完整食谱 - 用于生成食谱页面"""
        t = self.t
        
        # 显示食谱标题
        title = recipe_data.get('title', t('generated_recipe'))
        st.markdown(f"<h2 style='font-size: 1.8em;'>{title}</h2>", unsafe_allow_html=True)
        
        # 显示食谱描述
        if recipe_data.get('description'):
            st.markdown(f"### ℹ️ {t('recipe_description')}")
            st.markdown(recipe_data['description'])
        
        # 显示食材
        ingredients = recipe_data.get('ingredients', [])
        if ingredients:
            st.markdown(f"### 🥕 {t('ingredients')}")
            if isinstance(ingredients, list):
                for ingredient in ingredients:
                    st.markdown(f"- {ingredient}")
            else:
                st.markdown(ingredients)
        
        # 显示制作步骤
        instructions = recipe_data.get('instructions', [])
        if instructions:
            st.markdown(f"### 🍳 {t('instructions')}")
            if isinstance(instructions, list):
                for i, step in enumerate(instructions, 1):
                    st.markdown(f"{i}. {step}")
            else:
                st.markdown(instructions)
        
        # 显示营养信息
        self._display_nutrition_info(recipe_data)
        
        # 显示其他信息
        self._display_recipe_details(recipe_data)
        
        if show_save_options:
            self._display_save_options(recipe_data)
    
    def _display_nutrition_info(self, recipe_data):
        """显示营养信息"""
        t = self.t

        nutrition = NutritionAnalyzer()
        nutrition_info = nutrition.parse_nutrition(recipe_data)

        nutrition_dict = {}
        if isinstance(nutrition_info, dict):  # 如果已经是字典
            nutrition_dict = nutrition_info
        elif isinstance(nutrition_info, str):  # 如果是字符串
            for line in nutrition_info.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    cleaned_key = key.strip().strip('-').replace(' ', '')
                    nutrition_dict[cleaned_key] = value.strip()
                    
        # 显示营养信息
        nutrition_items = [
            ("🔥", t('calories'), nutrition_dict.get("Calories", nutrition_dict.get("卡路里", "N/A"))),
            ("🥩", t('protein'), nutrition_dict.get("Protein", nutrition_dict.get("蛋白质", "N/A"))),
            ("🥑", t('fat'), nutrition_dict.get("Fat", nutrition_dict.get("脂肪", "N/A"))),
            ("🌾", t('carbs'), nutrition_dict.get("Carbohydrates", nutrition_dict.get("碳水化合物", "N/A"))),
            ("🌱", t('fiber'), nutrition_dict.get("Fiber", nutrition_dict.get("纤维", "N/A"))),
            ("🍬", t('sugar'), nutrition_dict.get("Sugar", nutrition_dict.get("糖", "N/A"))),
            ("🧂", t('sodium'), nutrition_dict.get("Sodium", nutrition_dict.get("钠", "N/A"))),
            ("🧬", t('vitamin_a'), nutrition_dict.get("VitaminA", nutrition_dict.get("维生素A", "N/A"))),
            ("🦴", t('calcium'), nutrition_dict.get("Calcium", nutrition_dict.get("钙", "N/A"))),
            ("🩺", t('iron'), nutrition_dict.get("Iron", nutrition_dict.get("铁", "N/A")))
        ]
        
        # 如果有解析到的营养数据，显示卡片式布局
        if any(value != "N/A" for _, _, value in nutrition_items):
            cols = st.columns(3)
            for i, (icon, label, value) in enumerate(nutrition_items):
                with cols[i % 3]:
                    st.markdown(f"""
                    <div style="background-color: #f0f8ff; padding: 10px; margin: 5px 0; border-radius: 5px; text-align: center;">
                        <div style="font-size: 1.5em;">{icon}</div>
                        <div style="font-weight: bold; font-size: 0.9em;">{label}</div>
                        <div style="color: #666; font-size: 0.8em;">{value}</div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # 如果无法解析，直接显示原始文本
            st.text(nutrition_info)
    
    def _display_recipe_details(self, recipe_data):
        """显示食谱详细信息"""
        t = self.t
        
        details_info = []
        if recipe_data.get('serves'):
            details_info.append(f"**{t('serves')}**: {recipe_data['serves']}")
        if recipe_data.get('prep_time'):
            details_info.append(f"**{t('prep_time')}**: {recipe_data['prep_time']}")
        if recipe_data.get('cook_time'):
            details_info.append(f"**{t('cook_time')}**: {recipe_data['cook_time']}")
        if recipe_data.get('difficulty'):
            details_info.append(f"**{t('difficulty')}**: {recipe_data['difficulty']}")
        
        if details_info:
            st.markdown(" | ".join(details_info))
    
    def _display_save_options(self, recipe_data):
        """显示保存选项（表单形式）"""
        t = self.t
        
        st.markdown("---")
        st.markdown(f"### 💾 {t('save_options')}")
        
        with st.form("save_recipe_form"):
            col_save1, col_save2 = st.columns(2)
            
            with col_save1:
                rating = st.slider(t('rate_recipe'), 0, 5, 5, help=t('rate_help'))
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
            
            with col_action2:
                save_btn = st.form_submit_button(
                    t('save_recipe'),
                    type="primary",
                    use_container_width=True
                )
            
            with col_action3:
                # 下载按钮需要在表单外，或者使用html方式嵌入
                pass
            
            with col_action3:
                pass
            
            if save_btn:
                # 准备保存数据
                save_data = recipe_data.copy()
                save_data.update({
                    "rating": rating,
                    "tags": [tag.strip() for tag in tags_input.split(',') if tag.strip()],
                    "notes": notes
                })
                
                try:
                    recipe_id = st.session_state.db.save_recipe(st.session_state.username, save_data)
                    st.success(t('recipe_saved'))
                    st.balloons()    
                except Exception as e:
                    st.error(f"{t('save_error')}: {str(e)}")    

                st.session_state.recipe_data = None # 清空当前食谱数据
            
            
        
        # 下载按钮需要在表单外单独显示
        with st.container():
            col_download, _ = st.columns([1, 2])
            with col_download:
                self._display_download_button(recipe_data)
    
    

    def _display_download_button(self, recipe_data):
        """显示下载按钮"""
        t = self.t
        
        recipe_text = self._format_recipe_for_download(recipe_data)
        
        st.download_button(
            label=t('download_recipe'),
            data=recipe_text.encode('utf-8'),
            file_name=f"recipe_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    def _format_recipe_for_download(self, recipe_data):
        """格式化食谱用于下载"""
        t = self.t
        
        lines = []
        lines.append(t('recipe'))
        lines.append('=' * 50)
        lines.append('')
        
        if recipe_data.get('title'):
            lines.append(f"{t('recipe_title')}: {recipe_data['title']}")
            lines.append('')
        
        if recipe_data.get('description'):
            lines.append(t('recipe_description'))
            lines.append('-' * 50)
            lines.append(recipe_data['description'])
            lines.append('')
        
        # 食材
        ingredients = recipe_data.get('ingredients', [])
        if ingredients:
            lines.append(t('ingredients'))
            lines.append('-' * 50)
            if isinstance(ingredients, list):
                for ingredient in ingredients:
                    lines.append(f'- {ingredient}')
            else:
                lines.append(str(ingredients))
            lines.append('')
        
        # 制作步骤
        instructions = recipe_data.get('instructions', [])
        if instructions:
            lines.append(t('instructions'))
            lines.append('-' * 50)
            if isinstance(instructions, list):
                for i, step in enumerate(instructions, 1):
                    lines.append(f'{i}. {step}')
            else:
                lines.append(str(instructions))
            lines.append('')
        
        # 营养信息
        nutrition = NutritionAnalyzer()
        nutrition_info = nutrition.parse_nutrition(recipe_data)
        if nutrition_info:
            lines.append(t('nutrition_facts'))
            lines.append('-' * 50)
            lines.append(nutrition_info)
            lines.append('')
        
        # 其他信息
        lines.append('---')
        if recipe_data.get('serves'):
            lines.append(f"{t('serves')}: {recipe_data['serves']}")
        if recipe_data.get('prep_time'):
            lines.append(f"{t('prep_time')}: {recipe_data['prep_time']}")
        if recipe_data.get('cook_time'):
            lines.append(f"{t('cook_time')}: {recipe_data['cook_time']}")
        if recipe_data.get('difficulty'):
            lines.append(f"{t('difficulty')}: {recipe_data['difficulty']}")
        
        lines.append(f"{t('generated_on')}: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        
        return '\n'.join(lines)