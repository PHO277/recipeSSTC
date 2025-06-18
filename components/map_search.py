# components/map_search.py
import streamlit as st
import folium
from utils.translations import get_translation
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
import os
import random


class MapSearch:
    def __init__(self):
        # 地图API密钥
        try:
            self.amap_key = st.secrets.get("AMAP_API_KEY", "")
        except:
            self.amap_key = ""

        # 初始化 DeepSeek（复用项目中的 LLM）
        try:
            from llm_interface import LLMInterface
            deepseek_key = st.secrets.get("DEEPSEEK_API_KEY", "")
            if deepseek_key:
                self.llm = LLMInterface(deepseek_key)
            else:
                self.llm = None
        except:
            self.llm = None

        # 初始化用户位置
        if 'user_location' not in st.session_state:
            st.session_state.user_location = [39.9042, 116.4074]  # 默认北京

        # 初始化界面状态
        if 'selected_restaurant_id' not in st.session_state:
            st.session_state.selected_restaurant_id = None
        if 'show_navigation_for' not in st.session_state:
            st.session_state.show_navigation_for = None

        self.user_location = st.session_state.user_location

    def render_map_page(self):
        """渲染地图搜索页面"""
        lang = st.session_state.get('language', 'zh')
        
        st.title(f"🗺️ {get_translation('restaurant_map_search', lang)}")
        st.markdown(f"### {get_translation('search_dish_recommend_restaurant', lang)}")

        if not self.amap_key:
            st.info(f"ℹ️ {get_translation('tip', lang)}: {get_translation('using_mock_data_mode', lang)}")

        # 创建两列布局
        col1, col2 = st.columns([2, 3])

        with col1:
            self._render_search_panel()

        with col2:
            self._render_map()

        # 在主区域显示搜索结果（避免嵌套布局）
        if "search_results" in st.session_state and st.session_state.search_results:
            st.markdown("---")
            self._display_search_results()

    def _render_search_panel(self):
        """渲染搜索面板"""
        lang = st.session_state.get('language', 'zh')
        
        st.markdown(f"#### 🔍 {get_translation('search_dish', lang)}")

        # 搜索输入
        dish_name = st.text_input(
            get_translation('input_dish_name', lang),
            placeholder=get_translation('dish_example', lang),
            key="dish_search_input"
        )

        # 搜索选项
        with st.expander(get_translation('advanced_options', lang), expanded=False):
            search_radius = st.slider(
                get_translation('search_range_km', lang),
                min_value=1,
                max_value=10,
                value=3,
                key="search_radius"
            )

            price_range = st.select_slider(
                get_translation('price_range', lang),
                options=["💰", "💰💰", "💰💰💰", "💰💰💰💰"],
                value="💰💰",
                key="price_range"
            )

            min_rating = st.slider(
                get_translation('min_rating', lang),
                min_value=0.0,
                max_value=5.0,
                value=3.5,
                step=0.5,
                key="min_rating"
            )

        # 确保search_radius存在
        if 'search_radius' not in st.session_state:
            st.session_state.search_radius = 3
        search_radius = st.session_state.get('search_radius', 3)

        # 搜索按钮
        search_col1, search_col2 = st.columns(2)
        with search_col1:
            search_button = st.button(
                f"🔍 {get_translation('search_restaurants', lang)}",
                type="primary",
                use_container_width=True,
                key="search_restaurants_btn"
            )
        with search_col2:
            lucky_button = st.button(
                f"🎲 {get_translation('random_recommend', lang)}",
                use_container_width=True,
                key="lucky_search_btn"
            )

        # 处理搜索
        if search_button and dish_name:
            with st.spinner(get_translation('searching_restaurants', lang)):
                self._search_restaurants(dish_name, search_radius)
                if "search_results" in st.session_state and st.session_state.search_results:
                    st.success(get_translation('found_restaurants', lang).format(len(st.session_state.search_results)))
                else:
                    st.warning(get_translation('no_restaurants_found', lang))

        if lucky_button:
            # 随机菜品列表 - 根据语言选择
            if lang == 'en':
                random_dishes = ["Kung Pao Chicken", "Sweet and Sour Pork", "Fish-flavored Pork", "Hot Pot", "Sushi", "Ramen", "Pizza", "Burger"]
            elif lang == 'ja':
                random_dishes = ["宮保鶏丁", "糖醋排骨", "魚香肉絲", "火鍋", "寿司", "ラーメン", "ピザ", "ハンバーガー"]
            else:
                random_dishes = ["宫保鸡丁", "糖醋排骨", "鱼香肉丝", "麻辣香锅", "寿司", "拉面", "披萨", "汉堡"]
            
            random_dish = random.choice(random_dishes)
            st.info(f"🎲 {get_translation('random_recommend', lang)}: {random_dish}")

            with st.spinner(get_translation('searching_dish_restaurants', lang).format(random_dish)):
                self._search_restaurants(random_dish, search_radius)
                if "search_results" in st.session_state and st.session_state.search_results:
                    st.success(get_translation('found_restaurants', lang).format(len(st.session_state.search_results)))

    def _search_restaurants(self, dish_name, radius):
        """执行餐厅搜索流程"""
        try:
            # 1. 使用AI分析菜品类型
            cuisine_info = self._analyze_dish_cuisine(dish_name)

            # 2. 构建搜索关键词
            search_keywords = self._build_search_keywords(dish_name, cuisine_info)

            # 3. 调用地图API搜索
            results = []
            for keyword in search_keywords[:3]:  # 最多使用3个关键词
                restaurants = self._call_map_api(keyword, radius)
                results.extend(restaurants)

            # 4. 去重和排序
            unique_results = self._deduplicate_results(results)
            ranked_results = self._rank_results(unique_results, dish_name, cuisine_info)

            # 5. 保存结果
            st.session_state.search_results = ranked_results
            st.session_state.search_dish = dish_name
            st.session_state.cuisine_info = cuisine_info

        except Exception as e:
            st.error(f"搜索失败：{str(e)}")
            # 设置空结果
            st.session_state.search_results = []

    def _analyze_dish_cuisine(self, dish_name):
        """使用 DeepSeek 智能分析菜品"""
        lang = st.session_state.get('language', 'zh')
        
        # 如果没有 LLM，使用规则匹配
        if not self.llm:
            return self._analyze_dish_cuisine_fallback(dish_name)

        try:
            # 根据语言构建不同的 prompt
            if lang == 'en':
                prompt = f"""
                Please analyze the dish "{dish_name}" and return the result in JSON format:
                {{
                    "cuisine_type": "Cuisine type (e.g., Chinese, Japanese, Korean, Western, Hot Pot, etc.)",
                    "restaurant_types": ["List of recommended restaurant types, at least 3"],
                    "search_keywords": ["Search keywords for finding related restaurants"],
                    "dish_characteristics": {{
                        "spicy_level": "Spiciness (0-5)",
                        "price_range": "Price range (Low/Medium/High)",
                        "cooking_method": "Cooking method"
                    }},
                    "similar_dishes": ["List of similar dishes"],
                    "recommended_restaurant_names": ["Recommended restaurant name patterns"]
                }}

                Return only JSON, no other explanations.
                """
            else:
                prompt = f"""
                请分析菜品"{dish_name}"，返回JSON格式的结果：
                {{
                    "cuisine_type": "菜系类型（如：中餐、日料、韩餐、西餐、火锅等）",
                    "restaurant_types": ["推荐的餐厅类型列表，至少3个"],
                    "search_keywords": ["搜索关键词列表，用于查找相关餐厅"],
                    "dish_characteristics": {{
                        "spicy_level": "辣度（0-5）",
                        "price_range": "价格区间（低/中/高）",
                        "cooking_method": "烹饪方式"
                    }},
                    "similar_dishes": ["相似菜品列表"],
                    "recommended_restaurant_names": ["推荐的餐厅名称模式，如'川菜馆'、'家常菜馆'等"]
                }}

                只返回JSON，不要其他说明。
                """

            # 调用 LLM
            response = self.llm.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": get_translation('food_expert_system_prompt', lang)},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            # 解析响应
            result = response.choices[0].message.content.strip()
            # 清理可能的 markdown 标记
            if result.startswith("```json"):
                result = result[7:]
            if result.endswith("```"):
                result = result[:-3]

            cuisine_info = json.loads(result.strip())

            # 添加置信度
            cuisine_info['confidence'] = 0.95
            cuisine_info['analysis_method'] = 'deepseek_ai'

            return cuisine_info

        except Exception as e:
            st.warning(get_translation('ai_analysis_failed', lang).format(str(e)))
            return self._analyze_dish_cuisine_fallback(dish_name)

    def _analyze_dish_cuisine_fallback(self, dish_name):
        """备用的规则匹配方法"""
        cuisine_rules = {
            "中餐": ["炒", "煮", "蒸", "炖", "烧", "宫保", "鱼香", "麻婆", "糖醋", "红烧", "麻辣", "香锅"],
            "日料": ["寿司", "刺身", "拉面", "天妇罗", "照烧", "味增", "日本", "日式"],
            "韩餐": ["泡菜", "烤肉", "石锅", "冷面", "拌饭", "韩国", "韩式"],
            "西餐": ["披萨", "意面", "汉堡", "牛排", "沙拉", "薯条", "西式", "意大利"],
            "火锅": ["火锅", "串串", "麻辣烫", "冒菜"]
        }

        detected_cuisine = "中餐"  # 默认
        restaurant_types = ["中餐厅", "中国餐厅"]

        for cuisine, keywords in cuisine_rules.items():
            if any(keyword in dish_name for keyword in keywords):
                detected_cuisine = cuisine
                if cuisine == "中餐":
                    restaurant_types = ["中餐厅", "中国餐厅", "家常菜", "川菜", "粤菜"]
                elif cuisine == "日料":
                    restaurant_types = ["日本料理", "日料", "寿司店", "居酒屋"]
                elif cuisine == "韩餐":
                    restaurant_types = ["韩国料理", "韩餐", "烤肉店"]
                elif cuisine == "西餐":
                    restaurant_types = ["西餐厅", "牛排馆", "披萨店", "意大利餐厅"]
                elif cuisine == "火锅":
                    restaurant_types = ["火锅店", "火锅", "串串香"]
                break

        return {
            "cuisine_type": detected_cuisine,
            "restaurant_types": restaurant_types,
            "search_keywords": restaurant_types,
            "confidence": 0.85,
            "analysis_method": "rule_based"
        }

    def _build_search_keywords(self, dish_name, cuisine_info):
        """构建智能搜索关键词"""
        keywords = []

        # 如果是 AI 分析的结果，使用 AI 推荐的关键词
        if cuisine_info.get('search_keywords'):
            keywords.extend(cuisine_info['search_keywords'][:3])

        # 添加餐厅类型关键词
        keywords.extend(cuisine_info["restaurant_types"][:2])

        # 添加菜系关键词
        keywords.append(cuisine_info["cuisine_type"])

        # 如果有推荐的餐厅名称模式
        if cuisine_info.get('recommended_restaurant_names'):
            keywords.extend(cuisine_info['recommended_restaurant_names'][:2])

        # 去重
        keywords = list(dict.fromkeys(keywords))

        return keywords

    def _call_map_api(self, keyword, radius):
        """调用高德地图API"""
        if not self.amap_key:
            # 如果没有API key，返回模拟数据
            return self._get_mock_restaurants(keyword)

        try:
            # 确保radius是数字
            if isinstance(radius, (list, tuple)):
                radius = radius[0] if radius else 3
            else:
                radius = float(radius) if radius else 3

            url = "https://restapi.amap.com/v3/place/around"
            
            # 确保位置格式正确
            if isinstance(self.user_location, list) and len(self.user_location) >= 2:
                lat = self.user_location[0]
                lng = self.user_location[1]
            else:
                lat = 39.9042
                lng = 116.4074
            
            params = {
                'key': self.amap_key,
                'keywords': keyword,
                'location': f"{lng},{lat}",  # 高德要求：经度在前，纬度在后
                'radius': int(radius * 1000),  # 转换为米
                'types': '050000',  # 餐饮服务
                'sortrule': 'distance',
                'offset': 25,
                'page': 1,
                'extensions': 'all'
            }

            response = requests.get(url, params=params, timeout=5)
            data = response.json()

            if data['status'] == '1':
                pois = data.get('pois', [])
                results = []
                
                for poi in pois:
                    restaurant = {
                        'id': poi.get('id', ''),
                        'name': poi.get('name', ''),
                        'address': poi.get('address', ''),
                        'location': poi.get('location', ''),
                        'tel': poi.get('tel', ''),
                        'type': poi.get('type', ''),
                        'typecode': poi.get('typecode', ''),
                        'distance': int(float(poi.get('distance', 0))),
                        'biz_ext': poi.get('biz_ext', {})
                    }
                    
                    # 解析评分和价格
                    biz_ext = restaurant['biz_ext']
                    restaurant['rating'] = float(biz_ext.get('rating', 0)) if biz_ext.get('rating') else random.uniform(3.5, 5.0)
                    restaurant['avg_price'] = float(biz_ext.get('cost', 0)) if biz_ext.get('cost') else random.randint(30, 200)
                    
                    results.append(restaurant)
                
                return results
            else:
                st.warning(f"API返回错误: {data.get('info', '未知错误')}")
                return self._get_mock_restaurants(keyword)

        except Exception as e:
            st.warning(f"地图API调用失败，使用模拟数据: {str(e)}")
            return self._get_mock_restaurants(keyword)

    def _get_mock_restaurants(self, keyword):
        """获取模拟餐厅数据"""
        # 更真实的餐厅名称库
        restaurant_templates = {
            "火锅": ["海底捞火锅", "小龙坎火锅", "蜀大侠火锅", "大龙燚火锅", "德庄火锅"],
            "川菜": ["眉州东坡", "陈麻婆豆腐", "巴国布衣", "蜀香园", "川味观"],
            "烤鸭": ["全聚德", "便宜坊", "大董烤鸭", "四季民福", "利群烤鸭"],
            "日料": ["将太无二", "鮨然", "隐泉日料", "一风堂拉面", "味千拉面"],
            "西餐": ["王品牛排", "豪客来", "必胜客", "萨莉亚", "新元素"],
            "烧烤": ["很久以前", "丰茂烤串", "聚点串吧", "木屋烧烤", "串越时光"],
            "粤菜": ["陶陶居", "广州酒家", "炳胜品味", "点都德", "稻香"],
            "江浙菜": ["外婆家", "绿茶餐厅", "新白鹿", "弄堂里", "小南国"]
        }
        
        # 默认餐厅名
        default_names = [
            f"老王{keyword}馆", f"{keyword}大师", f"正宗{keyword}",
            f"{keyword}食府", f"阿姨{keyword}店", f"{keyword}小院"
        ]
        
        # 选择合适的餐厅名
        mock_restaurants = []
        found_template = False
        
        for cuisine, names in restaurant_templates.items():
            if cuisine in keyword or any(k in keyword for k in names):
                restaurant_names = names
                found_template = True
                break
        
        if not found_template:
            restaurant_names = default_names

        # 基于用户当前位置生成附近的餐厅
        base_lat, base_lng = self.user_location
        if isinstance(base_lat, list):
            base_lat = base_lat[0]
            base_lng = self.user_location[1]

        for i, name in enumerate(restaurant_names[:8]):
            # 在用户位置周围随机生成餐厅位置（约3公里范围内）
            lat_offset = random.uniform(-0.03, 0.03)
            lng_offset = random.uniform(-0.03, 0.03)
            
            lat = base_lat + lat_offset
            lng = base_lng + lng_offset

            # 计算大概的距离（简化计算）
            distance = int(((lat - base_lat) ** 2 + (lng - base_lng) ** 2) ** 0.5 * 111000)

            mock_restaurants.append({
                'id': f'mock_{keyword}_{i}',
                'name': name,
                'address': f"模拟地址 - {random.choice(['东路', '西街', '南巷', '北大道'])}{random.randint(1, 999)}号",
                'location': f"{lng},{lat}",
                'tel': f"{random.choice(['010', '021', '020', '0755'])}-{random.randint(10000000, 99999999)}",
                'rating': round(random.uniform(3.5, 5.0), 1),
                'avg_price': random.randint(30, 200),
                'distance': distance
            })

        return mock_restaurants

    def _deduplicate_results(self, results):
        """去除重复餐厅"""
        seen = set()
        unique = []

        for restaurant in results:
            restaurant_id = restaurant.get('id', restaurant.get('name', ''))
            if restaurant_id not in seen:
                seen.add(restaurant_id)
                unique.append(restaurant)

        return unique

    def _rank_results(self, results, dish_name, cuisine_info):
        """使用 AI 增强的排序算法"""
        scored_results = []

        for restaurant in results:
            score = 0

            # 基础评分逻辑
            name = restaurant.get('name', '')

            # 1. 餐厅类型匹配
            for restaurant_type in cuisine_info.get('restaurant_types', []):
                if restaurant_type in name:
                    score += 25
                    break

            # 2. 如果有推荐的餐厅名称模式，额外加分
            if cuisine_info.get('recommended_restaurant_names'):
                for pattern in cuisine_info['recommended_restaurant_names']:
                    if pattern in name:
                        score += 15
                        break

            # 3. 评分权重
            rating = float(restaurant.get('rating', 0))
            score += rating * 5

            # 4. 距离权重
            distance = int(restaurant.get('distance', 1000))
            score += max(0, 30 - distance / 100)

            # 5. 价格匹配（如果 AI 分析了价格区间）
            if cuisine_info.get('dish_characteristics', {}).get('price_range'):
                price_range = cuisine_info['dish_characteristics']['price_range']
                avg_price = restaurant.get('avg_price', 50)

                if price_range in ['低', 'Low'] and avg_price < 50:
                    score += 10
                elif price_range in ['中', 'Medium'] and 50 <= avg_price <= 100:
                    score += 10
                elif price_range in ['高', 'High'] and avg_price > 100:
                    score += 10

            # 添加详细信息
            restaurant['match_score'] = score
            restaurant['suggested_for'] = dish_name
            restaurant['cuisine_match'] = cuisine_info['cuisine_type']

            # 如果有 AI 分析的置信度，也加入考虑
            if cuisine_info.get('confidence', 0) > 0.9:
                restaurant['ai_recommended'] = True

            scored_results.append(restaurant)

        # 按分数排序
        return sorted(scored_results, key=lambda x: x['match_score'], reverse=True)

    def _display_search_results(self):
        """显示增强的搜索结果"""
        lang = st.session_state.get('language', 'zh')
        
        st.markdown(f"#### 📍 {get_translation('recommended_restaurants', lang)}")

        results = st.session_state.search_results
        dish_name = st.session_state.search_dish
        cuisine_info = st.session_state.cuisine_info

        # 显示搜索解释（包含 AI 分析信息）
        with st.expander(f"🤖 {get_translation('ai_analysis_result', lang)}", expanded=True):
            # 使用两列显示AI分析结果
            analysis_col1, analysis_col2 = st.columns(2)

            with analysis_col1:
                st.markdown(f"**{get_translation('search_dish', lang)}**: {dish_name}")
                st.markdown(f"**{get_translation('cuisine_recognition', lang)}**: {cuisine_info['cuisine_type']}")
                
                analysis_method = get_translation('ai_analysis', lang) if cuisine_info.get('analysis_method') == 'deepseek_ai' else get_translation('rule_matching', lang)
                st.markdown(f"**{get_translation('analysis_method', lang)}**: {analysis_method}")
                st.markdown(f"**{get_translation('confidence', lang)}**: {cuisine_info.get('confidence', 0) * 100:.1f}%")

            with analysis_col2:
                if cuisine_info.get('dish_characteristics'):
                    chars = cuisine_info['dish_characteristics']
                    st.markdown(f"**{get_translation('dish_characteristics', lang)}**:")
                    if chars.get('spicy_level'):
                        spicy_num = 3  # 默认值
                        try:
                            spicy_num = int(float(chars['spicy_level']))
                        except:
                            pass
                        st.markdown(f"- {get_translation('spicy_level', lang)}: {'🌶️' * spicy_num}")
                    if chars.get('price_range'):
                        st.markdown(f"- {get_translation('price_range', lang)}: {chars['price_range']}")
                    if chars.get('cooking_method'):
                        st.markdown(f"- {get_translation('cooking_method', lang)}: {chars['cooking_method']}")

            if cuisine_info.get('similar_dishes'):
                st.markdown(f"**{get_translation('similar_dishes', lang)}**: {', '.join(cuisine_info['similar_dishes'][:5])}")

        st.info(f"📊 {get_translation('found_restaurants', lang).format(len(results))}")

        # 显示餐厅列表 - 使用卡片式布局避免复杂的嵌套
        for idx, restaurant in enumerate(results[:10]):
            # 创建餐厅卡片
            with st.container():
                # 餐厅标题行
                ai_badge = "🤖 " if restaurant.get('ai_recommended') else ""
                st.markdown(f"### {ai_badge}{idx + 1}. {restaurant['name']}")
                
                # 餐厅信息行
                info_text = f"📍 {restaurant.get('address', get_translation('address_unknown', lang))} | "
                info_text += f"⭐ {restaurant.get('rating', 0)} | "
                info_text += f"💰 ¥{restaurant.get('avg_price', 'N/A')} | "
                
                if 'distance' in restaurant:
                    distance = restaurant['distance']
                    if distance < 1000:
                        info_text += f"📏 {distance}m"
                    else:
                        info_text += f"📏 {distance / 1000:.1f}km"
                
                st.markdown(info_text)

                # 操作按钮行 - 使用水平排列
                btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
                
                with btn_col1:
                    if st.button(f"📋 {get_translation('view_details', lang)}", key=f"detail_{idx}"):
                        st.session_state.selected_restaurant_id = restaurant['id']
                
                with btn_col2:
                    if st.button(f"🧭 {get_translation('navigate', lang)}", key=f"nav_{idx}"):
                        st.session_state.show_navigation_for = restaurant['id']
                
                with btn_col3:
                    if st.button(f"⭐ {get_translation('favorite', lang)}", key=f"fav_{idx}"):
                        self._add_to_favorites(restaurant)
                
                with btn_col4:
                    if st.session_state.show_navigation_for == restaurant['id']:
                        if st.button("❌ 关闭导航", key=f"close_nav_{idx}"):
                            st.session_state.show_navigation_for = None

                # 显示餐厅详情（如果被选中）
                if st.session_state.selected_restaurant_id == restaurant['id']:
                    self._show_restaurant_detail_inline(restaurant, idx)

                # 显示导航信息（如果被选中）
                if st.session_state.show_navigation_for == restaurant['id']:
                    self._show_navigation_inline(restaurant)

                st.divider()

    def _show_restaurant_detail_inline(self, restaurant, idx):
        """内联显示餐厅详情（避免嵌套布局）"""
        lang = st.session_state.get('language', 'zh')
        
        with st.expander(f"🍽️ {restaurant['name']} - {get_translation('detail_info', lang)}", expanded=True):
            # 基本信息
            st.markdown(f"**{get_translation('basic_info', lang)}**")
            st.write(f"📍 {get_translation('address', lang)}: {restaurant.get('address', get_translation('unknown', lang))}")
            st.write(f"📞 {get_translation('phone', lang)}: {restaurant.get('tel', get_translation('unknown', lang))}")
            st.write(f"⭐ {get_translation('rating', lang)}: {restaurant.get('rating', get_translation('no_rating', lang))}")
            st.write(f"💰 {get_translation('avg_price', lang)}: ¥{restaurant.get('avg_price', get_translation('unknown', lang))}")
            
            st.markdown("---")
            
            # 推荐信息
            st.markdown(f"**{get_translation('recommendation_info', lang)}**")
            st.write(f"🍽️ {get_translation('recommended_dish', lang)}: {restaurant.get('suggested_for', '')}")
            st.write(f"🏷️ {get_translation('cuisine_match', lang)}: {restaurant.get('cuisine_match', '')}")
            if restaurant.get('ai_recommended'):
                st.write(f"🤖 {get_translation('ai_recommended', lang)}")
            if 'distance' in restaurant:
                distance = restaurant['distance']
                if distance < 1000:
                    st.write(f"📏 {get_translation('distance', lang)}: {distance}m")
                else:
                    st.write(f"📏 {get_translation('distance', lang)}: {distance / 1000:.1f}km")

            # 关闭按钮
            if st.button("❌ 关闭详情", key=f"close_detail_{idx}"):
                st.session_state.selected_restaurant_id = None
                st.rerun()

    def _show_navigation_inline(self, restaurant):
        """内联显示导航信息"""
        lang = st.session_state.get('language', 'zh')
        
        if 'location' in restaurant:
            location = restaurant['location']
            restaurant_name = restaurant['name']
            
            with st.expander(f"🚗 {get_translation('navigation_options', lang)}", expanded=True):
                st.markdown(f"**{get_translation('choose_navigation', lang)}:**")

                # 准备导航链接
                amap_url = f"https://uri.amap.com/navigation?to={location},{restaurant_name}&mode=car&policy=1&src=myapp&coordinate=gaode&callnative=0"

                lng, lat = location.split(',')
                baidu_url = f"http://api.map.baidu.com/direction?destination=latlng:{lat},{lng}|name:{restaurant_name}&mode=driving&src=webapp.baidu.openAPIdemo"

                tx_url = f"https://apis.map.qq.com/uri/v1/routeplan?type=drive&to={restaurant_name}&tocoord={lat},{lng}"

                # 使用markdown显示导航链接
                st.markdown(f"- [📍 {get_translation('amap_navigation', lang)}]({amap_url})")
                st.markdown(f"- [📍 {get_translation('baidu_navigation', lang)}]({baidu_url})")
                st.markdown(f"- [📍 {get_translation('tencent_navigation', lang)}]({tx_url})")

    def _render_map(self):
        """渲染地图"""
        lang = st.session_state.get('language', 'zh')
        
        st.markdown(f"#### 🗺️ {get_translation('restaurant_locations', lang)}")

        # 城市选择
        if lang == 'en':
            cities = ["Beijing", "Shanghai", "Guangzhou", "Shenzhen", "Hangzhou", "Chengdu", "Wuhan", "Xi'an"]
            city_map = {"Beijing": "北京", "Shanghai": "上海", "Guangzhou": "广州", "Shenzhen": "深圳", 
                       "Hangzhou": "杭州", "Chengdu": "成都", "Wuhan": "武汉", "Xi'an": "西安"}
        elif lang == 'ja':
            cities = ["北京", "上海", "広州", "深セン", "杭州", "成都", "武漢", "西安"]
            city_map = {"北京": "北京", "上海": "上海", "広州": "广州", "深セン": "深圳",
                       "杭州": "杭州", "成都": "成都", "武漢": "武汉", "西安": "西安"}
        else:
            cities = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
            city_map = {city: city for city in cities}
        
        city = st.selectbox(
            get_translation('select_city', lang),
            cities,
            key="city_select"
        )

        # 根据城市更新位置
        city_locations = {
            "北京": [39.9042, 116.4074],
            "上海": [31.2304, 121.4737],
            "广州": [23.1291, 113.2644],
            "深圳": [22.5431, 114.0579],
            "杭州": [30.2741, 120.1551],
            "成都": [30.5728, 104.0668],
            "武汉": [30.5928, 114.3055],
            "西安": [34.2658, 108.9541]
        }

        city_cn = city_map.get(city, city)
        if city_cn in city_locations:
            self.user_location = city_locations[city_cn]
            st.session_state.user_location = self.user_location

        # 定位和地址输入
        if st.button(f"📍 {get_translation('use_current_location', lang)}", key="use_current_location"):
            st.info(get_translation('location_requires_https', lang))

        address = st.text_input(
            get_translation('or_input_address', lang), 
            placeholder=get_translation('address_example', lang), 
            key="address_input"
        )
        if address and st.button(get_translation('locate', lang), key="locate_btn"):
            # 使用地理编码API
            if self.amap_key:
                coords = self._geocode_address(address)
                if coords:
                    self.user_location = coords
                    st.session_state.user_location = coords
                    st.success(get_translation('location_success', lang))
                    st.rerun()
            else:
                st.info(f"{get_translation('located_at', lang)}: {address}")

        # 创建地图
        m = folium.Map(
            location=self.user_location,
            zoom_start=13,
            tiles='OpenStreetMap',
            control_scale=True
        )

        # 添加用户位置标记
        folium.Marker(
            location=self.user_location,
            popup=get_translation('your_location', lang),
            tooltip=get_translation('you_are_here', lang),
            icon=folium.Icon(color='green', icon='user', prefix='fa')
        ).add_to(m)

        # 如果有搜索结果，添加标记
        if "search_results" in st.session_state and st.session_state.search_results:
            # 显示搜索信息
            st.info(f"🔍 {get_translation('showing_search_results_on_map', lang).format(len(st.session_state.search_results))}")

            bounds = []

            for idx, restaurant in enumerate(st.session_state.search_results[:10]):
                # 解析位置
                if 'location' in restaurant:
                    location_str = restaurant['location']
                    try:
                        lng, lat = map(float, location_str.split(','))

                        # 创建HTML弹窗内容
                        html = f"""
                        <div style="font-family: Arial; width: 200px;">
                            <h4 style="color: #2196F3; margin: 5px 0;">{restaurant['name']}</h4>
                            <p style="margin: 5px 0;"><b>{get_translation('address', lang)}:</b> {restaurant.get('address', get_translation('unknown', lang))}</p>
                            <p style="margin: 5px 0;"><b>{get_translation('rating', lang)}:</b> ⭐ {restaurant.get('rating', get_translation('no_rating', lang))}</p>
                            <p style="margin: 5px 0;"><b>{get_translation('avg_price', lang)}:</b> ¥{restaurant.get('avg_price', get_translation('unknown', lang))}</p>
                            <p style="margin: 5px 0;"><b>{get_translation('recommended_for', lang)}:</b> {restaurant.get('suggested_for', '')}</p>
                        </div>
                        """

                        # 创建弹窗
                        popup = folium.Popup(html=html, max_width=250)

                        # 前三个用红色标记，其他用蓝色
                        color = 'red' if idx < 3 else 'blue'

                        # 创建标记
                        folium.Marker(
                            location=[lat, lng],
                            popup=popup,
                            tooltip=f"{idx + 1}. {restaurant['name']}",
                            icon=folium.Icon(
                                color=color,
                                icon='cutlery',
                                prefix='fa'
                            )
                        ).add_to(m)

                        bounds.append([lat, lng])

                    except Exception as e:
                        st.warning(get_translation('cannot_parse_location', lang).format(restaurant['name'], str(e)))

            # 调整地图视野以包含所有标记
            if bounds:
                bounds.append(self.user_location)  # 包含用户位置
                m.fit_bounds(bounds)

        # 显示地图
        st_folium(m, width=700, height=500, key="restaurant_map")

    def _geocode_address(self, address):
        """将地址转换为坐标"""
        if not self.amap_key:
            st.error("需要API密钥才能使用地址定位功能")
            return None

        try:
            url = "https://restapi.amap.com/v3/geocode/geo"
            params = {
                'key': self.amap_key,
                'address': address,
                'city': st.session_state.get('city_select', '北京')
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == '1' and data['geocodes']:
                location = data['geocodes'][0]['location']
                lng, lat = map(float, location.split(','))
                return [lat, lng]
            else:
                st.error("无法定位该地址")
                return None

        except Exception as e:
            st.error(f"地址解析失败: {str(e)}")
            return None

    def _add_to_favorites(self, restaurant):
        """添加到收藏"""
        lang = st.session_state.get('language', 'zh')
        
        if 'favorites' not in st.session_state:
            st.session_state.favorites = []

        # 检查是否已收藏
        if not any(fav['id'] == restaurant['id'] for fav in st.session_state.favorites):
            st.session_state.favorites.append(restaurant)
            st.success(get_translation('favorited', lang).format(restaurant['name']))

            # 如果用户已登录，保存到数据库
            if st.session_state.get('logged_in') and st.session_state.get('db_manager'):
                try:
                    # 创建收藏记录
                    favorite_data = {
                        'restaurant': restaurant,
                        'saved_at': datetime.now(),
                        'dish_searched': st.session_state.get('search_dish', ''),
                        'type': 'restaurant_favorite'
                    }
                    st.session_state.db_manager.save_recipe(
                        st.session_state.username,
                        favorite_data
                    )
                except Exception as e:
                    st.warning(get_translation('save_to_cloud_failed', lang))
        else:
            st.warning(get_translation('already_favorited', lang).format(restaurant['name']))
