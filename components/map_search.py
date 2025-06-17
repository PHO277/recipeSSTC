# components/map_search.py
import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
import json
from datetime import datetime
import os


# from utils.config_manager import ConfigManager  # 暂时注释掉

class MapSearch:
    def __init__(self):
        # 地图API密钥（需要在.env或secrets.toml中配置）
        try:
            self.amap_key = st.secrets.get("AMAP_API_KEY", "")
        except:
            self.amap_key = ""

        # 初始化用户位置（从session state获取或使用默认值）
        if 'user_location' not in st.session_state:
            st.session_state.user_location = [39.9042, 116.4074]  # 默认北京

        self.user_location = st.session_state.user_location

    def render_map_page(self):
        """渲染地图搜索页面"""
        st.title("🗺️ 餐厅地图搜索")
        st.markdown("### 搜索您想吃的菜品，智能推荐附近餐厅")

        if not self.amap_key:
            with st.info("ℹ️ 提示"):
                st.markdown("当前使用**模拟数据模式**。配置API密钥以使用真实地图数据。")

        # 创建两列布局
        col1, col2 = st.columns([2, 3])

        with col1:
            self._render_search_panel()

        with col2:
            self._render_map()

    def _render_search_panel(self):
        """渲染搜索面板"""
        st.markdown("#### 🔍 搜索菜品")

        # 搜索输入
        dish_name = st.text_input(
            "输入菜品名称",
            placeholder="例如：番茄炒蛋、麻婆豆腐、寿司...",
            key="dish_search_input"
        )

        # 搜索选项
        with st.expander("高级选项", expanded=False):
            search_radius = st.slider(
                "搜索范围（公里）",
                min_value=1,
                max_value=10,
                value=3,
                key="search_radius"
            )

            price_range = st.select_slider(
                "价格范围",
                options=["💰", "💰💰", "💰💰💰", "💰💰💰💰"],
                value="💰💰",
                key="price_range"
            )

            min_rating = st.slider(
                "最低评分",
                min_value=0.0,
                max_value=5.0,
                value=3.5,
                step=0.5,
                key="min_rating"
            )

        # 搜索按钮
        col1, col2 = st.columns(2)
        with col1:
            search_button = st.button(
                "🔍 搜索餐厅",
                type="primary",
                use_container_width=True,
                key="search_restaurants_btn"
            )
        with col2:
            lucky_button = st.button(
                "🎲 随机推荐",
                use_container_width=True,
                key="lucky_search_btn"
            )

        # 处理搜索
        if search_button and dish_name:
            with st.spinner("正在搜索相关餐厅..."):
                self._search_restaurants(dish_name, search_radius)

        if lucky_button:
            # 随机菜品列表
            random_dishes = ["宫保鸡丁", "糖醋排骨", "鱼香肉丝", "麻辣香锅", "寿司", "拉面", "披萨", "汉堡"]
            import random
            random_dish = random.choice(random_dishes)

            # 不要修改 session_state，而是直接显示和搜索
            st.info(f"🎲 随机推荐：{random_dish}")

            with st.spinner(f"正在搜索 {random_dish} 相关餐厅..."):
                self._search_restaurants(random_dish, search_radius)

        # 显示搜索结果
        if "search_results" in st.session_state and st.session_state.search_results:
            self._display_search_results()

    def _search_restaurants(self, dish_name, radius):
        """搜索餐厅"""
        try:
            # 1. 使用LLM分析菜品类型
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

    def _analyze_dish_cuisine(self, dish_name):
        """使用LLM分析菜品所属菜系"""
        # 这里暂时使用规则匹配，实际应调用LLM
        cuisine_rules = {
            "中餐": ["炒", "煮", "蒸", "炖", "烧", "宫保", "鱼香", "麻婆", "糖醋", "红烧"],
            "日料": ["寿司", "刺身", "拉面", "天妇罗", "照烧", "味增"],
            "韩餐": ["泡菜", "烤肉", "石锅", "冷面", "拌饭"],
            "西餐": ["披萨", "意面", "汉堡", "牛排", "沙拉", "薯条"],
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
            "confidence": 0.85
        }

    def _build_search_keywords(self, dish_name, cuisine_info):
        """构建搜索关键词"""
        keywords = []

        # 添加餐厅类型关键词
        keywords.extend(cuisine_info["restaurant_types"][:2])

        # 添加菜系关键词
        keywords.append(cuisine_info["cuisine_type"])

        return keywords

    def _call_map_api(self, keyword, radius):
        """调用高德地图API"""
        if not self.amap_key:
            # 如果没有API key，返回模拟数据
            return self._get_mock_restaurants(keyword)

        try:
            url = "https://restapi.amap.com/v3/place/text"
            params = {
                'key': self.amap_key,
                'keywords': keyword,
                'city': '北京',  # 可以根据用户位置动态设置
                'types': '050000',  # 餐饮服务
                'offset': 20
            }

            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] == '1':
                return data['pois']
            else:
                return []

        except Exception as e:
            st.warning(f"地图API调用失败，使用模拟数据")
            return self._get_mock_restaurants(keyword)

    def _get_mock_restaurants(self, keyword):
        """获取模拟餐厅数据"""
        import random

        mock_restaurants = []
        base_names = [
            f"老张{keyword}", f"香满楼{keyword}", f"{keyword}世家",
            f"正宗{keyword}馆", f"{keyword}小院", f"阿姨{keyword}",
            f"小李{keyword}店", f"美味{keyword}", f"{keyword}大王"
        ]

        # 基于用户当前位置生成附近的餐厅
        base_lat, base_lng = self.user_location

        for i, name in enumerate(base_names[:8]):
            # 在用户位置周围随机生成餐厅位置（约3公里范围内）
            lat = base_lat + random.uniform(-0.03, 0.03)
            lng = base_lng + random.uniform(-0.03, 0.03)

            # 计算大概的距离（简化计算）
            distance = int(((lat - base_lat) ** 2 + (lng - base_lng) ** 2) ** 0.5 * 111000)

            mock_restaurants.append({
                'id': f'mock_{i}',
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
            if restaurant['id'] not in seen:
                seen.add(restaurant['id'])
                unique.append(restaurant)

        return unique

    def _rank_results(self, results, dish_name, cuisine_info):
        """对搜索结果进行智能排序"""
        scored_results = []

        for restaurant in results:
            score = 0

            # 基于餐厅类型匹配
            name = restaurant.get('name', '')
            for restaurant_type in cuisine_info['restaurant_types']:
                if restaurant_type in name:
                    score += 20
                    break

            # 基于评分
            rating = float(restaurant.get('rating', 0))
            score += rating * 4

            # 基于距离（假设距离越近越好）
            distance = int(restaurant.get('distance', 1000))
            score += max(0, 20 - distance / 100)

            # 添加分数
            restaurant['match_score'] = score
            restaurant['suggested_for'] = dish_name
            scored_results.append(restaurant)

        # 按分数排序
        return sorted(scored_results, key=lambda x: x['match_score'], reverse=True)

    def _display_search_results(self):
        """显示搜索结果列表"""
        st.markdown("#### 📍 推荐餐厅")

        results = st.session_state.search_results
        dish_name = st.session_state.search_dish
        cuisine_info = st.session_state.cuisine_info

        # 显示搜索解释
        st.info(f"""
        🔍 搜索 "{dish_name}"

        🍽️ 识别菜系：{cuisine_info['cuisine_type']}

        📊 找到 {len(results)} 家相关餐厅
        """)

        # 显示餐厅列表
        for idx, restaurant in enumerate(results[:10]):  # 最多显示10个
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])

                with col1:
                    st.markdown(f"**{idx + 1}. {restaurant['name']}**")
                    st.caption(restaurant.get('address', '地址未知'))

                with col2:
                    rating = restaurant.get('rating', 0)
                    st.markdown(f"⭐ {rating}")
                    if 'avg_price' in restaurant:
                        st.markdown(f"💰 人均 ¥{restaurant['avg_price']}")

                with col3:
                    if 'distance' in restaurant:
                        distance = restaurant['distance']
                        if distance < 1000:
                            st.markdown(f"📍 {distance}m")
                        else:
                            st.markdown(f"📍 {distance / 1000:.1f}km")

                # 操作按钮
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button(f"查看详情", key=f"detail_{idx}"):
                        self._show_restaurant_detail(restaurant)
                with col2:
                    if st.button(f"导航", key=f"nav_{idx}"):
                        self._navigate_to_restaurant(restaurant)
                with col3:
                    if st.button(f"收藏", key=f"fav_{idx}"):
                        self._add_to_favorites(restaurant)

                st.divider()

    def _render_map(self):
        """渲染地图"""
        st.markdown("#### 🗺️ 餐厅位置")

        # 添加城市选择和定位控制
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            city = st.selectbox(
                "选择城市",
                ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"],
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

            if city in city_locations:
                self.user_location = city_locations[city]
                st.session_state.user_location = self.user_location

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
            popup="您的位置",
            tooltip="您在这里",
            icon=folium.Icon(color='green', icon='user', prefix='fa')
        ).add_to(m)

        # 如果有搜索结果，添加标记
        if "search_results" in st.session_state and st.session_state.search_results:
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
                            <p style="margin: 5px 0;"><b>地址:</b> {restaurant.get('address', '未知')}</p>
                            <p style="margin: 5px 0;"><b>评分:</b> ⭐ {restaurant.get('rating', '暂无')}</p>
                            <p style="margin: 5px 0;"><b>人均:</b> ¥{restaurant.get('avg_price', '未知')}</p>
                            <p style="margin: 5px 0;"><b>推荐:</b> {restaurant.get('suggested_for', '')}</p>
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
                        st.warning(f"无法解析餐厅位置: {restaurant['name']} - {str(e)}")

            # 调整地图视野以包含所有标记
            if bounds:
                bounds.append(self.user_location)  # 包含用户位置
                m.fit_bounds(bounds)

        # 显示地图
        st_folium(m, width=700, height=500, key="restaurant_map")

    def _show_restaurant_detail(self, restaurant):
        """显示餐厅详情"""
        st.session_state.selected_restaurant = restaurant
        st.info(f"查看 {restaurant['name']} 的详情")

    def _navigate_to_restaurant(self, restaurant):
        """导航到餐厅"""
        if 'location' in restaurant:
            location = restaurant['location']
            # 构建导航URL（这里使用高德地图网页版）
            nav_url = f"https://uri.amap.com/navigation?to={location},{restaurant['name']}&mode=car&policy=1&src=myapp&coordinate=gaode&callnative=0"
            st.markdown(f"[点击导航到 {restaurant['name']}]({nav_url})")

    def _add_to_favorites(self, restaurant):
        """添加到收藏"""
        if 'favorites' not in st.session_state:
            st.session_state.favorites = []

        st.session_state.favorites.append(restaurant)
        st.success(f"已收藏 {restaurant['name']}")