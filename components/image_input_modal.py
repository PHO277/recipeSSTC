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
import concurrent.futures
import threading
from typing import List, Dict, Tuple

class ImageInputModal:
    def __init__(self):
        self.api_key = st.secrets.get("SILICONFLOW_API_KEY", os.getenv("SILICONFLOW_API_KEY"))
        self.api_url = "https://api.siliconflow.cn/v1/chat/completions"
        self.model = "Qwen/Qwen2.5-VL-32B-Instruct"
        self.max_workers = 20  # 最大并发线程数
    
    def encode_image_to_base64(self, image):
        """将PIL图像转换为base64字符串"""
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def call_siliconflow_api_single(self, image_base64: str, language: str, image_name: str = "") -> Tuple[str, List[str]]:
        """为单张图片调用SILICONFLOW API识别食材"""
        if not self.api_key:
            raise Exception("SILICONFLOW_API_KEY not found")
        
        # 构建消息内容
        content = []
        
        # 统一的英语提示词，要求使用指定语言回复但保持JSON字段为英文
        unified_prompt = f"""Please identify all unique ingredients in this image and return them in a JSON format.
    Requirements:
    1. Respond in {language} language for the ingredient names
    2. Always use "ingredients" as the JSON field name (in English)
    3. Return only unique ingredients visible in this image (no duplicates)
    4. Format: {{"ingredients": ["ingredient1", "ingredient2", ...]}}
    5. If no ingredients are found in the image, return {{"ingredients": []}}"""
        
        content.append({
            "type": "text",
            "text": unified_prompt
        })
        
        # 添加单张图像
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_base64}"
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
            "max_tokens": 256,
            "temperature": 0.3,
            "top_p": 0.7,
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        max_retries = 1  # 最大重试次数
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                response = requests.post(self.api_url, json=payload, headers=headers, timeout=10)  #  设置超时时间为10秒
                
                print(f"图片 {image_name} API调用状态: {response.status_code}")  # 调试输出

                if response.status_code == 200:
                    try:
                        raw_content = response.json()['choices'][0]['message']['content']
                        ingredients = self._parse_ingredients_from_response(raw_content)
                        print(f"图片 {image_name} 识别到的食材: {ingredients}")
                        return image_name, ingredients
                        
                    except Exception as e:
                        print(f"图片 {image_name} API响应解析错误: {str(e)}")
                        return image_name, []
                else:
                    print(f"图片 {image_name} API调用失败: {response.status_code} - {response.text}")
                    return image_name, []
                    
            except requests.exceptions.Timeout:
                retry_count += 1
                if retry_count > max_retries:
                    print(f"图片 {image_name} API调用超时，已达到最大重试次数")
                    return image_name, []
                print(f"图片 {image_name} API调用超时，正在重试 ({retry_count}/{max_retries})")
                
            except Exception as e:
                print(f"图片 {image_name} API调用异常: {str(e)}")
                return image_name, []
    
    def _parse_ingredients_from_response(self, raw_content: str) -> List[str]:
        """从API响应中解析食材列表"""
        try:
            # 预处理：清理可能的截断问题
            raw_content = raw_content.strip()
            
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
                ingredients = ingredients_data.get('ingredients', [])
                
                # 清理食材列表中的重复项和空值
                cleaned_ingredients = []
                seen = set()
                for ingredient in ingredients:
                    if isinstance(ingredient, str):
                        # 清理换行符、制表符和多余空格
                        cleaned = re.sub(r'\s+', ' ', ingredient.strip())
                        if cleaned and cleaned not in seen:
                            cleaned_ingredients.append(cleaned)
                            seen.add(cleaned)
                
                return cleaned_ingredients
                
            except json.JSONDecodeError as e:
                # 如果JSON解析失败，尝试修复可能的截断问题
                print(f"JSON解析错误，尝试修复: {e}")
                print(f"原始内容: {repr(json_content)}")
                
                # 尝试提取可能的JSON部分
                json_start = json_content.find('{')
                json_end = json_content.rfind('}')
                
                if json_start != -1 and json_end != -1 and json_end > json_start:
                    # 提取看起来像JSON的部分
                    possible_json = json_content[json_start:json_end+1]
                    
                    # 尝试修复常见的截断问题
                    if '"ingredients":' in possible_json:
                        # 检查数组是否完整
                        array_start = possible_json.find('[', possible_json.find('"ingredients":'))
                        if array_start != -1:
                            # 查找数组结束位置
                            bracket_count = 0
                            array_end = -1
                            for i in range(array_start, len(possible_json)):
                                if possible_json[i] == '[':
                                    bracket_count += 1
                                elif possible_json[i] == ']':
                                    bracket_count -= 1
                                    if bracket_count == 0:
                                        array_end = i
                                        break
                            
                            if array_end == -1:
                                # 数组没有正确结束，尝试修复
                                if possible_json.endswith('"') or possible_json.endswith('",'):
                                    possible_json = possible_json.rstrip('",') + '"]}'
                                elif not possible_json.endswith(']'):
                                    possible_json = possible_json.rstrip() + ']}'
                                else:
                                    possible_json = possible_json + '}'
                    
                    try:
                        ingredients_data = json.loads(possible_json)
                        ingredients = ingredients_data.get('ingredients', [])
                        
                        # 清理结果
                        cleaned_ingredients = []
                        seen = set()
                        for ingredient in ingredients:
                            if isinstance(ingredient, str):
                                cleaned = re.sub(r'\s+', ' ', ingredient.strip())
                                if cleaned and cleaned not in seen:
                                    cleaned_ingredients.append(cleaned)
                                    seen.add(cleaned)
                        
                        return cleaned_ingredients
                        
                    except json.JSONDecodeError:
                        print("修复后的JSON仍然无法解析")
                
                # 如果修复失败，尝试正则表达式提取
                ingredients_list = []
                # 查找引号包围的文本，但排除 "ingredients" 字段名
                ingredient_pattern = r'"([^"]+)"'
                matches = re.findall(ingredient_pattern, json_content)
                
                for match in matches:
                    # 过滤掉字段名和非食材内容
                    if match.lower() not in ['ingredients', 'ingredient'] and len(match) > 1:
                        cleaned = re.sub(r'\s+', ' ', match.strip())
                        if cleaned and cleaned not in ingredients_list:
                            ingredients_list.append(cleaned)
                
                return ingredients_list
                
        except Exception as e:
            print(f"解析响应内容时发生错误: {str(e)}")
            print(f"原始内容: {repr(raw_content)}")
            return []
    
    def call_siliconflow_api_parallel(self, images_data: List[Tuple[str, str]], language: str) -> Dict[str, List[str]]:
        """并行调用SILICONFLOW API识别多张图片的食材"""
        results = {}
        results_lock = threading.Lock()  # 添加线程锁保护结果字典
        
        # 使用线程池并行处理
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务，确保每个任务都有唯一标识
            future_to_image = {}
            for idx, (image_name, image_base64) in enumerate(images_data):
                # 为每张图片创建唯一标识，避免重复文件名问题
                unique_image_name = f"{image_name}_{idx}" if image_name else f"image_{idx}"
                future = executor.submit(self.call_siliconflow_api_single, image_base64, language, unique_image_name)
                future_to_image[future] = (unique_image_name, image_name)  # 保存原始名称用于显示
            
            # 收集结果
            completed_count = 0
            for future in concurrent.futures.as_completed(future_to_image):
                unique_image_name, original_image_name = future_to_image[future]
                try:
                    result_name, ingredients = future.result()
                    
                    # 使用线程锁保护结果字典的写入
                    with results_lock:
                        # 使用原始文件名作为显示键名，但确保不重复
                        display_name = original_image_name
                        counter = 1
                        while display_name in results:
                            display_name = f"{original_image_name}_{counter}"
                            counter += 1
                        
                        results[display_name] = ingredients
                        completed_count += 1
                        print(f"完成处理 ({completed_count}/{len(images_data)}): {display_name} -> {len(ingredients)} 个食材")
                        
                except Exception as e:
                    print(f"处理图片 {unique_image_name} 时发生错误: {str(e)}")
                    with results_lock:
                        results[original_image_name] = []
        
        print(f"并行处理完成，共处理 {len(results)} 张图片")
        return results
    
    def merge_ingredients_from_results(self, results: Dict[str, List[str]]) -> List[str]:
        """合并多张图片的识别结果，去重并返回唯一食材列表"""
        all_ingredients = set()
        total_ingredient_count = 0
        
        print(f"开始合并 {len(results)} 张图片的识别结果...")
        
        for image_name, ingredients in results.items():
            if ingredients:
                #print(f"图片 '{image_name}' 贡献的食材 ({len(ingredients)}个): {ingredients}")
                # 清理食材名称，去除可能的特殊字符和重复项
                cleaned_ingredients = []
                for ingredient in ingredients:
                    # 清理换行符和多余空格
                    cleaned = ingredient.strip().replace('\n', '').replace('\r', '')
                    if cleaned and cleaned not in cleaned_ingredients:
                        cleaned_ingredients.append(cleaned)
                
                all_ingredients.update(cleaned_ingredients)
                total_ingredient_count += len(cleaned_ingredients)
            else:
                print(f"图片 '{image_name}': 未识别到食材")
        
        # 转换为列表并排序
        unique_ingredients = sorted(list(all_ingredients))
        
        print(f"合并统计:")
        print(f"- 总计识别到食材: {total_ingredient_count} 个")
        print(f"- 去重后唯一食材: {len(unique_ingredients)} 个")
        print(f"- 最终食材列表: {unique_ingredients}")
        
        return unique_ingredients
    
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
        if 'recognition_results' not in st.session_state:
            st.session_state.recognition_results = {}
        
        # 图像识别按钮
        if st.button("📷 " + t('image_recognition'), key="image_btn"):
            st.session_state.show_image_modal = True
            st.session_state.uploaded_images = []
            st.session_state.recognized_ingredients = []
            st.session_state.ingredient_selections = {}
            st.session_state.recognition_results = {}
        
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
                                    # 准备图像数据
                                    images_data = []
                                    for idx, uploaded_file in enumerate(st.session_state.uploaded_images):
                                        try:
                                            image = Image.open(uploaded_file)
                                            # 调整图像大小以减少API调用成本
                                            image.thumbnail((800, 600), Image.Resampling.LANCZOS)
                                            img_base64 = self.encode_image_to_base64(image)
                                            # 使用索引确保文件名唯一性
                                            unique_name = f"{uploaded_file.name}_{idx}" if uploaded_file.name else f"image_{idx}"
                                            images_data.append((uploaded_file.name, img_base64))  # 保持原始名称用于API调用
                                        except Exception as e:
                                            st.error(f"Error when processing {uploaded_file.name} : {str(e)}")
                                            continue
                                    
                                    if not images_data:
                                        st.error(t('no_valid_images'))
                                        return
                                    
                                    # 并行调用API识别食材E
                                    recognition_results = self.call_siliconflow_api_parallel(images_data, st.session_state.language)
                                    st.session_state.recognition_results = recognition_results
                                    
                                    
                                    # 合并所有图片的识别结果
                                    all_ingredients = self.merge_ingredients_from_results(recognition_results)
                                    
                                    
                                    if not all_ingredients:
                                        st.warning(t('no_ingredients_detected'))
                                        
                                        return
                                    
                                    st.session_state.recognized_ingredients = all_ingredients
                                    
                                    # 初始化选择状态（默认全不选）
                                    st.session_state.ingredient_selections = {
                                        ingredient: False for ingredient in all_ingredients
                                    }
                                    
                                    st.rerun()
                                    
                                except Exception as e:
                                    st.error(f"{t('recognition_error')}: {str(e)}")
                    
                    with col3:
                        if st.button(t('cancel')):
                            st.session_state.show_image_modal = False
                            st.rerun()
                
                # 如果有识别结果，显示食材选择界面
                else:
                    st.markdown(f"**{t('recognized_ingredients')}:**")
                    
                    '''
                    # 显示识别统计信息
                    if st.session_state.recognition_results:
                        with st.expander("📊 识别详情", expanded=False):
                            total_images = len(st.session_state.recognition_results)
                            successful_images = sum(1 for ingredients in st.session_state.recognition_results.values() if ingredients)
                            total_ingredients = len(st.session_state.recognized_ingredients)
                            
                            st.write(f"- 处理图片数量: {total_images}")
                            st.write(f"- 成功识别图片: {successful_images}")
                            st.write(f"- 识别到的唯一食材数量: {total_ingredients}")
                            
                            st.markdown("**各图片详细结果:**")
                            for image_name, ingredients in st.session_state.recognition_results.items():
                                if ingredients:
                                    st.write(f"- **{image_name}**: {', '.join(ingredients)}")
                                else:
                                    st.write(f"- **{image_name}**: 未识别到食材")'''
                    
                    # 显示食材复选框（每行4个）
                    ingredients_list = st.session_state.recognized_ingredients

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