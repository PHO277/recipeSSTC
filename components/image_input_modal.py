import streamlit as st # type: ignore
import base64
import requests # type: ignore
import json
import os
import random
from PIL import Image # type: ignore
import io
from utils.translations import get_translation
import re

class ImageInputModal:
    def __init__(self):
        self.api_key = st.secrets.get("SILICONFLOW_API_KEY", os.getenv("SILICONFLOW_API_KEY"))
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = "Qwen/Qwen2.5-VL-32B-Instruct"
    
    def encode_image_to_base64(self, uploaded_file):
        """将上传的文件转换为base64字符串"""
        try:
            # Read the file content first
            file_content = uploaded_file.read()
            # Then create an image from the bytes
            image = Image.open(io.BytesIO(file_content))
            # Convert to JPEG format in memory
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return img_str
        except Exception as e:
            print(f"Error processing image {uploaded_file.name}: {str(e)}")
            raise
    
    def call_siliconflow_api(self, images, language):
        """调用SILICONFLOW API识别食材"""
        if not self.api_key:
            raise Exception("SILICONFLOW_API_KEY not found")
        
        # 构建消息内容
        content = []
        
        # 统一的英语提示词，要求使用指定语言回复但保持JSON字段为英文
        unified_prompt = f"""Please identify all unique ingredients in the image and return them in a JSON format. 
        Requirements:
        1. Respond in {language} language for the ingredient names
        2. Always use "ingredients" as the JSON field name (in English)
        3. Return only unique ingredients (no duplicates)
        4. Format: {{"ingredients": ["ingredient1", "ingredient2", ...]}}
        5. If no ingredients are found, return {{"ingredients": []}}"""
        
        content.append({
            "type": "text",
            "text": unified_prompt
        })
        
        # 添加图像
        for img_base64 in images:
            content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{img_base64}"
                }
            })
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": content
                }
            ],
            "stream": False,
            "max_tokens": 512,
            "temperature": 0.3,
            "top_p": 0.7,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(self.api_url, json=payload, headers=headers)

        print(response.status_code, response.text)  # 调试输出

        if response.status_code == 200:
            try:
                raw_content = response.json()['choices'][0]['message']['content']
                
                # 尝试从 ```json ... ``` 块中提取JSON内容
                json_match = re.search(r'```json\n(.*?)\n```', raw_content, re.DOTALL)
                if json_match:
                    json_content = json_match.group(1)
                else:
                    # 如果没有找到 ```json``` 块，假设 raw_content 本身是 JSON
                    json_content = raw_content.strip()
                
                # 尝试解析JSON
                try:
                    ingredients_data = json.loads(json_content)
                    return ingredients_data.get('ingredients', [])
                except json.JSONDecodeError as e:
                    # 如果JSON解析失败，尝试修复可能的截断问题
                    print(f"JSON解析错误，尝试修复可能截断的响应: {e}")
                    
                    # 尝试提取可能的JSON部分
                    json_start = json_content.find('{')
                    json_end = json_content.rfind('}')
                    
                    if json_start != -1 and json_end != -1 and json_end > json_start:
                        # 提取看起来像JSON的部分
                        possible_json = json_content[json_start:json_end+1]
                        
                        # 尝试补全可能的缺失部分
                        if '"ingredients":' in possible_json and ']' not in possible_json:
                            # 如果缺少闭合的数组和对象
                            possible_json = possible_json.rstrip() + ']}'
                        elif '"ingredients":' in possible_json and possible_json.endswith('"'):
                            # 如果缺少闭合的数组和对象，但最后一个字符是引号
                            possible_json = possible_json.rstrip('"') + '"]}'
                        
                        try:
                            ingredients_data = json.loads(possible_json)
                            return ingredients_data.get('ingredients', [])
                        except json.JSONDecodeError:
                            pass
                    
                    # 如果修复失败，尝试更简单的提取方式
                    ingredients_list = []
                    # 查找类似 "ingredient" 的文本模式
                    ingredient_matches = re.findall(r'"(?!ingredients)[^"]+"', json_content)
                    if ingredient_matches:
                        ingredients_list = [match.strip('"') for match in ingredient_matches]
                    
                    if ingredients_list:
                        return ingredients_list
                    
                    # 如果所有方法都失败，返回空列表
                    return []
                    
            except Exception as e:
                print(f"API错误: {str(e)}")
                raise Exception(f"API调用失败: {str(e)}")
    
    def render_modal(self):
        """渲染图像输入模态窗口"""
        t = lambda key: get_translation(key, st.session_state.language)
        
        if 'show_image_modal' not in st.session_state:
            st.session_state.show_image_modal = False
        if 'uploaded_images' not in st.session_state:
            st.session_state.uploaded_images = []
        if 'recognized_ingredients' not in st.session_state:
            st.session_state.recognized_ingredients = []
        if 'ingredient_selections' not in st.session_state:
            st.session_state.ingredient_selections = {}
        
        # 图像识别按钮
        if st.button("📷 " + t('image_recognition'), key="image_btn"):
            st.session_state.show_image_modal = True
            st.session_state.uploaded_images = []
            st.session_state.recognized_ingredients = []
            st.session_state.ingredient_selections = {}
        
        # 模态窗口
        if st.session_state.show_image_modal:
            with st.container():
                st.markdown("---")
                st.markdown(f"### 📷 {t('image_ingredient_recognition')}")
                
                # 如果还没有识别结果，显示图像上传界面
                if not st.session_state.recognized_ingredients:
                    uploaded_files = st.file_uploader(
                        t('upload_images'),
                        type=['png', 'jpg', 'jpeg'],
                        accept_multiple_files=True,
                        key="image_uploader"
                    )
                    
                    if uploaded_files:
                        st.session_state.uploaded_images = uploaded_files
                        
                        # 显示上传的图像缩略图
                        if st.session_state.uploaded_images:
                            st.markdown(f"**{t('uploaded_images')}:**")
                            num_rows = (len(st.session_state.uploaded_images) + 3) // 4
                            
                            for row in range(num_rows):
                                cols = st.columns(4)
                                images_in_row = st.session_state.uploaded_images[row*4 : (row+1)*4]
                                
                                for idx, uploaded_file in enumerate(images_in_row):
                                    with cols[idx]:
                                        try:
                                            # Read the file content first
                                            file_content = uploaded_file.read()
                                            # Then create an image from the bytes
                                            image = Image.open(io.BytesIO(file_content))
                                            st.image(image, caption=uploaded_file.name, width=150)
                                            # Reset file pointer to beginning
                                            uploaded_file.seek(0)
                                        except Exception as e:
                                            st.error(f"无法显示图像 {uploaded_file.name}: {str(e)}")
                                            continue
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
                    with col1:
                        if st.button(t('start_recognition'), type="primary", disabled=not st.session_state.uploaded_images):
                            with st.spinner(t('recognizing_ingredients')):
                                try:
                                    # 转换图像为base64
                                    images_base64 = []
                                    for uploaded_file in st.session_state.uploaded_images:
                                        try:
                                            img_base64 = self.encode_image_to_base64(uploaded_file)
                                            images_base64.append(img_base64)
                                        except Exception as e:
                                            st.error(f"无法处理图像 {uploaded_file.name}: {str(e)}")
                                            continue
                                    
                                    if not images_base64:
                                        st.error(t('no_valid_images'))
                                        return
                                    
                                    # 调用API识别食材
                                    ingredients = self.call_siliconflow_api(images_base64, st.session_state.language)
                                    if not ingredients:  # 明确检查API返回的食材列表是否为空
                                        st.warning(t('no_ingredients_detected'))
                                        return
                                    st.session_state.recognized_ingredients = ingredients
                                    
                                    # 初始化选择状态（默认全不选）
                                    st.session_state.ingredient_selections = {
                                        ingredient: False for ingredient in ingredients
                                    }
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"{t('recognition_error')}: {str(e)}")
                    
                    with col2:
                        if st.button(t('cancel')):
                            st.session_state.show_image_modal = False
                            st.rerun()
                
                # 如果有识别结果，显示食材选择界面
                else:
                    
                    st.markdown(f"**{t('recognized_ingredients')}:**")
                    
                    # 显示食材复选框（每行4个）
                    # 使用集合来存储已识别的食材，自动去重
                    unique_ingredients = set(st.session_state.recognized_ingredients)

                    # 转换为列表以便按顺序显示
                    ingredients_list = list(unique_ingredients)

                    # 显示复选框
                    for i in range(0, len(ingredients_list), 4):
                        cols = st.columns(4)
                        for j, ingredient in enumerate(ingredients_list[i:i+4]):
                            with cols[j]:
                                st.session_state.ingredient_selections[ingredient] = st.checkbox(
                                    ingredient,
                                    value=st.session_state.ingredient_selections.get(ingredient, False),
                                    key=f"ingredient_{ingredient}"
                                )

                    # 底部按钮区域
                    st.markdown("")  # Add an empty line below the checkboxes
                    col_select, col_random, col_add, col_cancel = st.columns([1, 1, 1, 1])

                    with col_select:
                        # 检查当前是否全部选中
                        all_selected = all(st.session_state.ingredient_selections.values()) if st.session_state.ingredient_selections else False
                        select_all = st.checkbox(t('select_all'), value=all_selected, key="select_all_ingredients")
                        
                        # 当全选状态改变时，更新所有食材的选择状态
                        if select_all != all_selected:
                            for ingredient in st.session_state.ingredient_selections:
                                st.session_state.ingredient_selections[ingredient] = select_all
                            st.rerun()

                    with col_random:
                        if st.button("🎲", help=t('random_select')):
                            available_ingredients = st.session_state.recognized_ingredients
                            num_available = len(available_ingredients)
                            
                            if num_available == 0:
                                st.warning(t('no_ingredients_to_select'))
                            else:
                                # Determine how many to select (1-4, but no more than available)
                                max_to_select = min(4, num_available)
                                min_to_select = min(2, max_to_select)  # Don't try to select 2 if only 1 is available
                                num_to_select = random.randint(min_to_select, max_to_select)
                                
                                selected_ingredients = random.sample(available_ingredients, num_to_select)
                                
                                # 清空当前选择
                                for ingredient in st.session_state.ingredient_selections:
                                    st.session_state.ingredient_selections[ingredient] = False
                                
                                # 随机选择
                                for ingredient in selected_ingredients:
                                    st.session_state.ingredient_selections[ingredient] = True
                                st.rerun()

                    with col_add:
                        if st.button(t('add_ingredients'), type="primary"):
                            selected_ingredients = [
                                ingredient for ingredient, selected 
                                in st.session_state.ingredient_selections.items() 
                                if selected
                            ]
                            
                            # 将选中的食材添加到输入框
                            if 'ingredient_input' not in st.session_state:
                                st.session_state.ingredient_input = ""
                            
                            if selected_ingredients:
                                if st.session_state.ingredient_input.strip():
                                    st.session_state.ingredient_input += ", " + ", ".join(selected_ingredients)
                                else:
                                    st.session_state.ingredient_input = ", ".join(selected_ingredients)
                            
                            st.session_state.show_image_modal = False
                            st.rerun()

                    with col_cancel:
                        if st.button(t('cancel')):
                            st.session_state.show_image_modal = False
                            st.rerun()

                st.markdown("---")
        
        return st.session_state.get('ingredient_input', '')