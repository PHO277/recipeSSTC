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

        self.user_location = st.session_state.user_location

    def render_map_page(self):
        """渲染地图搜索页面"""
        lang = st.session_state.get('language', 'zh')
        
        st.title(f"🗺️ {get_translation('restaurant_map_search', lang)}")
        st.markdown(f"### {get_translation('search_dish_recommend_restaurant', lang)}")

        if not self.amap_key:
            with st.info(f"ℹ️ {get_translation('tip', lang)}"):
                st.markdown(get_translation('using_mock_data_mode', lang))

        # 创建两列布局
        col1, col2 = st.columns([2, 3])

        with col1:
            self._render_search_panel()

        with col2:
            self._render_map()

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
        if 'search_radius' not in st.session_state:
            st.session_state.search_radius = 3
        # 获取search_radius的值（如果高级选项未展开，使用默认值）
        search_radius = st.session_state.get('search_radius', 3)

        # 搜索按钮
        col1, col2 = st.columns(2)
        with col1:
            search_button = st.button(
                f"🔍 {get_translation('search_restaurants', lang)}",
                type="primary",
                use_container_width=True,
                key="search_restaurants_btn"
            )
        with col2:
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

            # 不要修改 session_state，而是直接显示和搜索
            st.info(f"🎲 {get_translation('random_recommend', lang)}: {random_dish}")

            with st.spinner(get_translation('searching_dish_restaurants', lang).format(random_dish)):
                self._search_restaurants(random_dish, search_radius)
                if "search_results" in st.session_state and st.session_state.search_results:
                    st.success(get_translation('found_restaurants', lang).format(len(st.session_state.search_results)))

        # 显示搜索结果
        if "search_results" in st.session_state and st.session_state.search_results:
            self._display_search_results()

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

    def _display_search_results(self):
        """显示增强的搜索结果"""
        lang = st.session_state.get('language', 'zh')
        
        st.markdown(f"#### 📍 {get_translation('recommended_restaurants', lang)}")

        results = st.session_state.search_results
        dish_name = st.session_state.search_dish
        cuisine_info = st.session_state.cuisine_info

        # 显示搜索解释（包含 AI 分析信息）
        with st.expander(f"🤖 {get_translation('ai_analysis_result', lang)}", expanded=True):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**{get_translation('search_dish', lang)}**: {dish_name}")
                st.markdown(f"**{get_translation('cuisine_recognition', lang)}**: {cuisine_info['cuisine_type']}")
                
                analysis_method = get_translation('ai_analysis', lang) if cuisine_info.get('analysis_method') == 'deepseek_ai' else get_translation('rule_matching', lang)
                st.markdown(f"**{get_translation('analysis_method', lang)}**: {analysis_method}")
                st.markdown(f"**{get_translation('confidence', lang)}**: {cuisine_info.get('confidence', 0) * 100:.1f}%")

            with col2:
                if cuisine_info.get('dish_characteristics'):
                    chars = cuisine_info['dish_characteristics']
                    st.markdown(f"**{get_translation('dish_characteristics', lang)}**:")
                    if chars.get('spicy_level'):
                        st.markdown(f"- {get_translation('spicy_level', lang)}: {'🌶️' * int(chars['spicy_level'])}")
                    if chars.get('price_range'):
                        st.markdown(f"- {get_translation('price_range', lang)}: {chars['price_range']}")
                    if chars.get('cooking_method'):
                        st.markdown(f"- {get_translation('cooking_method', lang)}: {chars['cooking_method']}")

            if cuisine_info.get('similar_dishes'):
                st.markdown(f"**{get_translation('similar_dishes', lang)}**: {', '.join(cuisine_info['similar_dishes'][:5])}")

        st.info(f"📊 {get_translation('found_restaurants', lang).format(len(results))}")

        # 显示餐厅列表
        for idx, restaurant in enumerate(results[:10]):
            with st.container():
                # 餐厅信息使用单独的容器
                restaurant_container = st.container()
                with restaurant_container:
                    col1, col2, col3 = st.columns([3, 2, 1])

                    with col1:
                        # 如果是 AI 推荐的，加个标记
                        ai_badge = "🤖 " if restaurant.get('ai_recommended') else ""
                        st.markdown(f"**{ai_badge}{idx + 1}. {restaurant['name']}**")
                        st.caption(restaurant.get('address', get_translation('address_unknown', lang)))

                    with col2:
                        rating = restaurant.get('rating', 0)
                        st.markdown(f"⭐ {rating}")
                        if 'avg_price' in restaurant:
                            st.markdown(f"💰 {get_translation('avg_price', lang)} ¥{restaurant['avg_price']}")

                    with col3:
                        if 'distance' in restaurant:
                            distance = restaurant['distance']
                            if distance < 1000:
                                st.markdown(f"📍 {distance}m")
                            else:
                                st.markdown(f"📍 {distance / 1000:.1f}km")

                # 操作按钮使用独立的容器，避免嵌套
                button_container = st.container()
                with button_container:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(get_translation('view_details', lang), key=f"detail_{idx}"):
                            self._show_restaurant_detail(restaurant)
                    with col2:
                        if st.button(get_translation('navigate', lang), key=f"nav_{idx}"):
                            # 不要在这里直接调用会创建columns的方法
                            st.session_state['navigate_to'] = restaurant
                            st.rerun()
                    with col3:
                        if st.button(get_translation('favorite', lang), key=f"fav_{idx}"):
                            self._add_to_favorites(restaurant)

                st.divider()

    def _render_map(self):
        """渲染地图"""
        lang = st.session_state.get('language', 'zh')
        
        st.markdown(f"#### 🗺️ {get_translation('restaurant_locations', lang)}")

        # 添加城市选择和定位控制
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            # 根据语言显示城市名称
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

        with col2:
            # 添加手动输入位置
            if st.button(f"📍 {get_translation('use_current_location', lang)}", key="use_current_location"):
                st.info(get_translation('location_requires_https', lang))

        with col3:
            # 地址输入
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

    def _show_restaurant_detail(self, restaurant):
        """显示餐厅详情"""
        lang = st.session_state.get('language', 'zh')
        
        st.session_state.selected_restaurant = restaurant

        # 不使用 expander，直接显示
        st.markdown(f"### 🍽️ {restaurant['name']} - {get_translation('detail_info', lang)}")
        
        # 基本信息和推荐信息分两列显示
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**{get_translation('basic_info', lang)}**")
            st.write(f"📍 {get_translation('address', lang)}: {restaurant.get('address', get_translation('unknown', lang))}")
            st.write(f"📞 {get_translation('phone', lang)}: {restaurant.get('tel', get_translation('unknown', lang))}")
            st.write(f"⭐ {get_translation('rating', lang)}: {restaurant.get('rating', get_translation('no_rating', lang))}")
            st.write(f"💰 {get_translation('avg_price', lang)}: ¥{restaurant.get('avg_price', get_translation('unknown', lang))}")

        with col2:
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
        
        st.divider()

    def _navigate_to_restaurant(self, restaurant):
        """导航到餐厅 - 使用expander避免布局冲突"""
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

                # 使用列表形式展示
                st.markdown(f"- [📍 {get_translation('amap_navigation', lang)}]({amap_url})")
                st.markdown(f"- [📍 {get_translation('baidu_navigation', lang)}]({baidu_url})")
                st.markdown(f"- [📍 {get_translation('tencent_navigation', lang)}]({tx_url})")

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
