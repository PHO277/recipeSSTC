import streamlit as st
from datetime import datetime
from utils.translations import get_translation
from nutrition_analyzer import NutritionAnalyzer
from text_to_speech import render_tts_component_improved, render_tts_component_simple

class RecipeDisplay:
    def __init__(self):
        self.t = lambda key: get_translation(key, st.session_state.language)
    
    def display_full_recipe(self, recipe_data, show_save_options=True, enable_tts=True):
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
        
        # 添加语音功能 - 在保存选项之前显示
        if enable_tts:
            self._display_tts_section(recipe_data)
        
        if show_save_options:
            self._display_save_options(recipe_data)
    
    def _display_tts_section(self, recipe_data):
        """显示语音播报功能"""
        t = self.t
        
        st.markdown("---")
        
        # 创建语音内容
        tts_text = self._format_recipe_for_tts(recipe_data)
        
        # 提供TTS选项选择
        tts_option = st.radio(
            "🔊 语音播报模式",
            options=["简化版", "完整版"],
            horizontal=True,
            help="简化版重点显示文本内容，完整版提供多种语音选项"
        )
        
        # 根据选择显示相应的TTS组件
        if tts_option == "简化版":
            render_tts_component_simple(
                text=tts_text, 
                language=st.session_state.get('language', 'zh'),
                key="recipe_simple"
            )
        else:
            render_tts_component_improved(
                text=tts_text,
                language=st.session_state.get('language', 'zh'), 
                key="recipe_full"
            )
    
    def _format_recipe_for_tts(self, recipe_data):
        """格式化食谱内容用于语音播报"""
        t = self.t
        
        tts_parts = []
        
        # 标题
        if recipe_data.get('title'):
            tts_parts.append(f"{t('recipe_title')}: {recipe_data['title']}")
        
        # 描述
        if recipe_data.get('description'):
            tts_parts.append(f"{t('recipe_description')}: {recipe_data['description']}")
        
        # 食材
        ingredients = recipe_data.get('ingredients', [])
        if ingredients:
            tts_parts.append(f"{t('ingredients')}:")
            if isinstance(ingredients, list):
                for ingredient in ingredients:
                    tts_parts.append(ingredient)
            else:
                tts_parts.append(str(ingredients))
        
        # 制作步骤
        instructions = recipe_data.get('instructions', [])
        if instructions:
            tts_parts.append(f"{t('instructions')}:")
            if isinstance(instructions, list):
                for i, step in enumerate(instructions, 1):
                    tts_parts.append(f"第{i}步: {step}")
            else:
                tts_parts.append(str(instructions))
        
        # 其他信息
        detail_parts = []
        if recipe_data.get('serves'):
            detail_parts.append(f"{t('serves')}: {recipe_data['serves']}")
        if recipe_data.get('prep_time'):
            detail_parts.append(f"{t('prep_time')}: {recipe_data['prep_time']}")
        if recipe_data.get('cook_time'):
            detail_parts.append(f"{t('cook_time')}: {recipe_data['cook_time']}")
        if recipe_data.get('difficulty'):
            detail_parts.append(f"{t('difficulty')}: {recipe_data['difficulty']}")
        
        if detail_parts:
            tts_parts.extend(detail_parts)
        
        return " ".join(tts_parts)
    
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
    
    def display_recipe_with_custom_tts(self, recipe_data, tts_mode="simple", show_save_options=True):
        """显示食谱并提供自定义TTS选项"""
        t = self.t
        
        # 显示完整食谱内容（不包含默认TTS）
        self.display_full_recipe(recipe_data, show_save_options=show_save_options, enable_tts=False)
        
        # 自定义TTS部分
        st.markdown("---")
        st.markdown("### 🎙️ 语音播报功能")
        
        # 创建语音内容
        tts_text = self._format_recipe_for_tts(recipe_data)
        
        if tts_mode == "simple":
            render_tts_component_simple(
                text=tts_text,
                language=st.session_state.get('language', 'zh'),
                key="custom_simple"
            )
        elif tts_mode == "advanced":
            render_tts_component_improved(
                text=tts_text,
                language=st.session_state.get('language', 'zh'),
                key="custom_advanced"
            )
        else:
            # 允许用户选择TTS模式
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔊 简化版朗读", use_container_width=True):
                    render_tts_component_simple(
                        text=tts_text,
                        language=st.session_state.get('language', 'zh'),
                        key="custom_choice_simple"
                    )
            with col2:
                if st.button("🎯 完整版朗读", use_container_width=True):
                    render_tts_component_improved(
                        text=tts_text,
                        language=st.session_state.get('language', 'zh'),
                        key="custom_choice_advanced"
                    )